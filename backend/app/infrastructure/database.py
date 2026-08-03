"""
AI Freight Copilot — Database Connection Management.

Manages async connections to SQL Server (ERP, read-only) and PostgreSQL (app state).
Implements connection pooling, tenant isolation, and safety guards.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings, get_settings
from app.domain.value_objects import SQLResult

logger = structlog.get_logger(__name__)


# ── Dangerous SQL patterns that must never execute against the ERP ───────────
BLOCKED_PATTERNS = [
    "INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ", "CREATE ",
    "TRUNCATE ", "EXEC ", "EXECUTE ", "MERGE ", "GRANT ", "REVOKE ",
    "DENY ", "sp_", "xp_",
]


class DatabaseManager:
    """Manages database connections for ERP (read-only) and app state."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._erp_engine: AsyncEngine | None = None
        self._app_engine: AsyncEngine | None = None
        self._app_session_factory: async_sessionmaker[AsyncSession] | None = None
        # Tenant-specific ERP engines
        self._tenant_engines: dict[str, AsyncEngine] = {}

    async def initialize(self) -> None:
        """Initialize database connections."""
        logger.info("Initializing database connections")

        # App state database (PostgreSQL)
        self._app_engine = create_async_engine(
            self._settings.postgres_async_url,
            pool_size=self._settings.postgres_pool_size,
            max_overflow=self._settings.postgres_max_overflow,
            echo=self._settings.app_debug,
        )
        self._app_session_factory = async_sessionmaker(
            self._app_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Default ERP database (SQL Server) — READ ONLY
        try:
            self._erp_engine = create_async_engine(
                self._settings.sqlserver_async_url,
                pool_size=self._settings.sqlserver_pool_size,
                max_overflow=self._settings.sqlserver_max_overflow,
                pool_timeout=self._settings.sqlserver_pool_timeout,
                echo=self._settings.app_debug,
            )
            logger.info("ERP database engine created", database=self._settings.sqlserver_database)
        except Exception as e:
            logger.warning("ERP database connection deferred", error=str(e))

        logger.info("Database connections initialized")

    async def shutdown(self) -> None:
        """Close all database connections."""
        logger.info("Shutting down database connections")

        if self._erp_engine:
            await self._erp_engine.dispose()

        if self._app_engine:
            await self._app_engine.dispose()

        for engine in self._tenant_engines.values():
            await engine.dispose()

        self._tenant_engines.clear()
        logger.info("Database connections closed")

    # ── App State (PostgreSQL) ───────────────────────────────────────────

    @asynccontextmanager
    async def app_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async session for the app state database."""
        if not self._app_session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        async with self._app_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # ── ERP Database (SQL Server — READ ONLY) ────────────────────────────

    def _validate_query_safety(self, query: str) -> None:
        """Ensure the query is read-only. NEVER allow writes to ERP."""
        query_upper = query.upper().strip()
        for pattern in BLOCKED_PATTERNS:
            if pattern in query_upper:
                raise PermissionError(
                    f"BLOCKED: Write operations are not allowed on the ERP database. "
                    f"Detected forbidden pattern: '{pattern.strip()}'"
                )

    def _get_erp_engine(self, tenant_id: str | None = None) -> AsyncEngine:
        """Get the ERP engine for a tenant or the default."""
        if tenant_id and tenant_id in self._tenant_engines:
            return self._tenant_engines[tenant_id]
        if self._erp_engine:
            return self._erp_engine
        raise RuntimeError("ERP database not connected. Check SQL Server configuration.")

    async def execute_erp_query(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        max_rows: int = 1000,
    ) -> SQLResult:
        """
        Execute a READ-ONLY query against the ERP database.
        
        Safety: All queries are validated before execution.
        Returns structured SQLResult with timing information.
        """
        self._validate_query_safety(query)

        engine = self._get_erp_engine(tenant_id)
        start_time = time.monotonic()

        try:
            async with engine.connect() as conn:
                result = await conn.execute(text(query), params or {})
                columns = list(result.keys()) if result.returns_rows else []
                rows_raw = result.fetchall() if result.returns_rows else []

                is_truncated = len(rows_raw) > max_rows
                rows = [
                    dict(zip(columns, row))
                    for row in rows_raw[:max_rows]
                ]

                elapsed = (time.monotonic() - start_time) * 1000

                logger.info(
                    "ERP query executed",
                    query_preview=query[:100],
                    row_count=len(rows),
                    elapsed_ms=round(elapsed, 2),
                    tenant_id=tenant_id,
                )

                return SQLResult(
                    query=query,
                    columns=columns,
                    rows=rows,
                    row_count=len(rows),
                    execution_time_ms=round(elapsed, 2),
                    is_truncated=is_truncated,
                )

        except PermissionError:
            raise
        except Exception as e:
            elapsed = (time.monotonic() - start_time) * 1000
            logger.error("ERP query failed", error=str(e), query_preview=query[:100])
            return SQLResult(
                query=query,
                error=str(e),
                execution_time_ms=round(elapsed, 2),
            )

    async def get_erp_schema_info(self, tenant_id: str | None = None) -> SQLResult:
        """Retrieve the complete schema information from SQL Server."""
        query = """
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        return await self.execute_erp_query(query, tenant_id=tenant_id, max_rows=5000)

    async def get_erp_columns_info(
        self, table_name: str, schema_name: str = "dbo", tenant_id: str | None = None
    ) -> SQLResult:
        """Retrieve column information for a specific table."""
        query = """
        SELECT 
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.IS_NULLABLE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.COLUMN_DEFAULT,
            CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END AS IS_PRIMARY_KEY,
            fk.REFERENCED_TABLE_NAME,
            fk.REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN (
            SELECT ku.TABLE_NAME, ku.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
            WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        ) pk ON c.TABLE_NAME = pk.TABLE_NAME AND c.COLUMN_NAME = pk.COLUMN_NAME
        LEFT JOIN (
            SELECT 
                cu.TABLE_NAME AS SOURCE_TABLE,
                cu.COLUMN_NAME AS SOURCE_COLUMN,
                ku.TABLE_NAME AS REFERENCED_TABLE_NAME,
                ku.COLUMN_NAME AS REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
            JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE cu
                ON rc.CONSTRAINT_NAME = cu.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                ON rc.UNIQUE_CONSTRAINT_NAME = ku.CONSTRAINT_NAME
        ) fk ON c.TABLE_NAME = fk.SOURCE_TABLE AND c.COLUMN_NAME = fk.SOURCE_COLUMN
        WHERE c.TABLE_SCHEMA = :schema_name AND c.TABLE_NAME = :table_name
        ORDER BY c.ORDINAL_POSITION
        """
        return await self.execute_erp_query(
            query,
            params={"schema_name": schema_name, "table_name": table_name},
            tenant_id=tenant_id,
            max_rows=500,
        )

    async def get_erp_stored_procedures(self, tenant_id: str | None = None) -> SQLResult:
        """Retrieve stored procedure information."""
        query = """
        SELECT 
            SCHEMA_NAME(p.schema_id) AS schema_name,
            p.name AS procedure_name,
            p.create_date,
            p.modify_date
        FROM sys.procedures p
        ORDER BY p.name
        """
        return await self.execute_erp_query(query, tenant_id=tenant_id, max_rows=1000)

    async def get_table_row_count(
        self, table_name: str, schema_name: str = "dbo", tenant_id: str | None = None
    ) -> int:
        """Get approximate row count for a table."""
        query = """
        SELECT SUM(p.rows) AS row_count
        FROM sys.tables t
        JOIN sys.partitions p ON t.object_id = p.object_id
        WHERE t.name = :table_name 
          AND SCHEMA_NAME(t.schema_id) = :schema_name
          AND p.index_id IN (0, 1)
        """
        result = await self.execute_erp_query(
            query,
            params={"table_name": table_name, "schema_name": schema_name},
            tenant_id=tenant_id,
        )
        if result.rows:
            return int(result.rows[0].get("row_count", 0) or 0)
        return 0

    # ── Tenant Engine Management ─────────────────────────────────────────

    async def register_tenant_engine(
        self, tenant_id: str, connection_url: str
    ) -> None:
        """Register a new tenant-specific ERP database connection."""
        engine = create_async_engine(
            connection_url,
            pool_size=3,
            max_overflow=5,
            pool_timeout=30,
        )
        self._tenant_engines[tenant_id] = engine
        logger.info("Tenant ERP engine registered", tenant_id=tenant_id)

    async def remove_tenant_engine(self, tenant_id: str) -> None:
        """Remove and dispose a tenant engine."""
        if tenant_id in self._tenant_engines:
            await self._tenant_engines[tenant_id].dispose()
            del self._tenant_engines[tenant_id]
            logger.info("Tenant ERP engine removed", tenant_id=tenant_id)


# ── Module-level singleton ───────────────────────────────────────────────────

_db_manager: DatabaseManager | None = None


def get_database_manager() -> DatabaseManager:
    """Get the database manager singleton."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
