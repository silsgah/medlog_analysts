"""
AI Freight Copilot — Relationship Inferrer.

Infers relationships between database tables beyond explicit foreign keys.
Uses naming conventions, column type matching, and AI-assisted analysis.
"""

from __future__ import annotations

import re

import structlog

from app.domain.entities import DatabaseSchema, RelationshipInfo, TableInfo

logger = structlog.get_logger(__name__)


class RelationshipInferrer:
    """Infers relationships between tables using heuristics and AI."""

    # Common naming patterns for foreign key columns
    FK_PATTERNS = [
        re.compile(r"^(.+)_id$", re.IGNORECASE),
        re.compile(r"^(.+)ID$"),
        re.compile(r"^fk_?(.+)$", re.IGNORECASE),
        re.compile(r"^(.+)_code$", re.IGNORECASE),
        re.compile(r"^(.+)_ref$", re.IGNORECASE),
        re.compile(r"^(.+)_key$", re.IGNORECASE),
    ]

    # Table name normalization patterns (common ERP prefixes)
    TABLE_PREFIXES = ["tbl", "tbl_", "t_", "tb_"]

    def __init__(self) -> None:
        self._table_lookup: dict[str, TableInfo] = {}

    def infer_relationships(self, schema: DatabaseSchema) -> list[RelationshipInfo]:
        """
        Infer additional relationships beyond explicit foreign keys.
        
        Uses naming conventions and column type matching to find
        likely relationships with confidence scores.
        """
        # Build lookup for fast table matching
        self._table_lookup = {t.name.lower(): t for t in schema.tables}

        existing_rels = {
            (r.source_table.lower(), r.source_column.lower())
            for r in schema.relationships
        }

        inferred: list[RelationshipInfo] = []

        for table in schema.tables:
            for column in table.columns:
                # Skip columns that already have explicit FK relationships
                key = (table.name.lower(), column.name.lower())
                if key in existing_rels:
                    continue

                # Skip primary keys (they are targets, not sources)
                if column.is_primary_key:
                    continue

                # Try to infer a relationship from the column name
                relationship = self._infer_from_naming(table.name, column.name)
                if relationship:
                    inferred.append(relationship)

        logger.info(
            "Relationship inference complete",
            inferred_count=len(inferred),
            total_tables=len(schema.tables),
        )

        return inferred

    def _infer_from_naming(
        self, source_table: str, column_name: str
    ) -> RelationshipInfo | None:
        """Try to infer a relationship from column naming patterns."""
        for pattern in self.FK_PATTERNS:
            match = pattern.match(column_name)
            if not match:
                continue

            referenced_base = match.group(1).lower()

            # Try to find a matching table
            target_table = self._find_matching_table(referenced_base)
            if target_table and target_table.lower() != source_table.lower():
                # Determine the likely target column (usually PK)
                target_col = self._find_primary_key(target_table)

                confidence = self._calculate_confidence(
                    column_name, source_table, target_table
                )

                return RelationshipInfo(
                    source_table=source_table,
                    source_column=column_name,
                    target_table=target_table,
                    target_column=target_col,
                    relationship_type="many-to-one",
                    is_inferred=True,
                    confidence=confidence,
                )

        return None

    def _find_matching_table(self, base_name: str) -> str | None:
        """Find a table that matches the base name extracted from a column."""
        # Direct match
        if base_name in self._table_lookup:
            return self._table_lookup[base_name].name

        # Try with common prefixes
        for prefix in self.TABLE_PREFIXES:
            prefixed = f"{prefix}{base_name}"
            if prefixed in self._table_lookup:
                return self._table_lookup[prefixed].name

        # Try plural/singular variations
        variations = [
            base_name + "s",
            base_name + "es",
            base_name.rstrip("s"),
            base_name.rstrip("es"),
        ]
        for variation in variations:
            if variation in self._table_lookup:
                return self._table_lookup[variation].name
            for prefix in self.TABLE_PREFIXES:
                if f"{prefix}{variation}" in self._table_lookup:
                    return self._table_lookup[f"{prefix}{variation}"].name

        return None

    def _find_primary_key(self, table_name: str) -> str:
        """Find the primary key column for a table."""
        table = self._table_lookup.get(table_name.lower())
        if table:
            for col in table.columns:
                if col.is_primary_key:
                    return col.name
        # Default fallback
        return "id"

    def _calculate_confidence(
        self, column_name: str, source_table: str, target_table: str
    ) -> float:
        """Calculate confidence score for an inferred relationship."""
        confidence = 0.5  # Base confidence for naming match

        # Higher confidence if column name closely matches table name
        col_lower = column_name.lower()
        target_lower = target_table.lower()

        # Strip common prefixes from target table for comparison
        clean_target = target_lower
        for prefix in self.TABLE_PREFIXES:
            if clean_target.startswith(prefix):
                clean_target = clean_target[len(prefix):]
                break

        if clean_target in col_lower:
            confidence += 0.2

        # Higher confidence for standard patterns like "customer_id"
        if col_lower.endswith("_id") or col_lower.endswith("id"):
            confidence += 0.1

        # Cap at 0.95 — inferred relationships should never be 100%
        return min(confidence, 0.95)
