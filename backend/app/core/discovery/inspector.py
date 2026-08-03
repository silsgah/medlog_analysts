"""
AI Freight Copilot — Database Schema Inspector.

Connects to SQL Server and introspects the entire schema:
tables, views, columns, constraints, stored procedures, and relationships.
"""

from __future__ import annotations

import structlog

from app.domain.entities import (
    ColumnInfo,
    DatabaseSchema,
    RelationshipInfo,
    StoredProcedureInfo,
    TableInfo,
)
from app.infrastructure.database import DatabaseManager

logger = structlog.get_logger(__name__)


class SchemaInspector:
    """Introspects SQL Server database schema."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager

    async def inspect_full_schema(self, tenant_id: str | None = None) -> DatabaseSchema:
        """
        Perform a complete schema inspection of the SQL Server database.
        
        Discovers all tables, views, columns, constraints, stored procedures,
        and foreign key relationships.
        """
        logger.info("Starting full schema inspection", tenant_id=tenant_id)

        # Step 1: Get all tables and views
        tables_result = await self._db.get_erp_schema_info(tenant_id=tenant_id)
        if tables_result.error:
            logger.error("Failed to retrieve schema info", error=tables_result.error)
            raise RuntimeError(f"Schema inspection failed: {tables_result.error}")

        tables: list[TableInfo] = []
        views: list[TableInfo] = []

        for row in tables_result.rows:
            table_name = row["TABLE_NAME"]
            schema_name = row.get("TABLE_SCHEMA", "dbo")
            table_type = row.get("TABLE_TYPE", "BASE TABLE")

            # Step 2: Get columns for each table/view
            columns = await self._inspect_columns(table_name, schema_name, tenant_id)

            # Step 3: Get approximate row count
            row_count = 0
            if "VIEW" not in table_type.upper():
                row_count = await self._db.get_table_row_count(
                    table_name, schema_name, tenant_id
                )

            table_info = TableInfo(
                schema_name=schema_name,
                name=table_name,
                table_type="VIEW" if "VIEW" in table_type.upper() else "TABLE",
                columns=columns,
                row_count=row_count,
            )

            if table_info.table_type == "VIEW":
                views.append(table_info)
            else:
                tables.append(table_info)

        # Step 4: Get stored procedures
        stored_procedures = await self._inspect_stored_procedures(tenant_id)

        # Step 5: Extract foreign key relationships from column info
        relationships = self._extract_relationships(tables)

        schema = DatabaseSchema(
            tables=tables,
            views=views,
            stored_procedures=stored_procedures,
            relationships=relationships,
        )

        logger.info(
            "Schema inspection complete",
            tables=len(tables),
            views=len(views),
            stored_procedures=len(stored_procedures),
            relationships=len(relationships),
            tenant_id=tenant_id,
        )

        return schema

    async def _inspect_columns(
        self, table_name: str, schema_name: str, tenant_id: str | None
    ) -> list[ColumnInfo]:
        """Inspect columns for a specific table."""
        result = await self._db.get_erp_columns_info(table_name, schema_name, tenant_id)
        if result.error:
            logger.warning(
                "Failed to inspect columns",
                table=table_name,
                error=result.error,
            )
            return []

        columns = []
        for row in result.rows:
            columns.append(
                ColumnInfo(
                    name=row["COLUMN_NAME"],
                    data_type=row["DATA_TYPE"],
                    is_nullable=row.get("IS_NULLABLE", "YES") == "YES",
                    is_primary_key=bool(row.get("IS_PRIMARY_KEY", 0)),
                    is_foreign_key=row.get("REFERENCED_TABLE_NAME") is not None,
                    max_length=row.get("CHARACTER_MAXIMUM_LENGTH"),
                    default_value=row.get("COLUMN_DEFAULT"),
                    references_table=row.get("REFERENCED_TABLE_NAME"),
                    references_column=row.get("REFERENCED_COLUMN_NAME"),
                )
            )

        return columns

    async def _inspect_stored_procedures(
        self, tenant_id: str | None
    ) -> list[StoredProcedureInfo]:
        """Inspect all stored procedures."""
        result = await self._db.get_erp_stored_procedures(tenant_id=tenant_id)
        if result.error:
            logger.warning("Failed to inspect stored procedures", error=result.error)
            return []

        procedures = []
        for row in result.rows:
            procedures.append(
                StoredProcedureInfo(
                    schema_name=row.get("schema_name", "dbo"),
                    name=row["procedure_name"],
                )
            )

        return procedures

    def _extract_relationships(self, tables: list[TableInfo]) -> list[RelationshipInfo]:
        """Extract relationships from foreign key constraints found in columns."""
        relationships = []

        for table in tables:
            for column in table.columns:
                if column.is_foreign_key and column.references_table:
                    relationships.append(
                        RelationshipInfo(
                            source_table=table.name,
                            source_column=column.name,
                            target_table=column.references_table,
                            target_column=column.references_column or "id",
                            relationship_type="many-to-one",
                            is_inferred=False,
                            confidence=1.0,
                        )
                    )

        return relationships
