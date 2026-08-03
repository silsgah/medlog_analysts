"""
AI Freight Copilot — Knowledge Graph Builder.

Builds a business knowledge graph from discovered schema,
identifying primary entities and their interconnections.
"""

from __future__ import annotations

from datetime import datetime

import structlog

from app.domain.entities import (
    BusinessConcept,
    DatabaseSchema,
    KnowledgeGraph,
    RelationshipInfo,
    TableInfo,
)

logger = structlog.get_logger(__name__)


# Primary entity indicators — tables matching these patterns are flagged as primary
PRIMARY_ENTITY_KEYWORDS = {
    "customer", "client", "invoice", "receipt", "payment",
    "expense", "withdrawal", "job", "shipment", "container",
    "agent", "branch", "user", "employee", "order",
    "vendor", "supplier", "account", "transaction",
}

# Category classification based on table/column content
CATEGORY_RULES: dict[str, list[str]] = {
    "finance": ["invoice", "receipt", "payment", "expense", "withdrawal",
                "account", "ledger", "journal", "tax", "vat", "currency",
                "cashbook", "cash_book", "bank"],
    "operations": ["job", "shipment", "container", "cargo", "freight",
                   "delivery", "route", "vehicle", "driver", "fuel",
                   "tracking", "booking", "manifest"],
    "customers": ["customer", "client", "contact", "company", "debtor"],
    "hr": ["employee", "user", "staff", "payroll", "salary", "leave"],
    "audit": ["audit", "log", "history", "trail"],
    "master": ["branch", "department", "region", "country", "port",
               "agent", "vendor", "supplier", "currency"],
}


class KnowledgeGraphBuilder:
    """Builds a business knowledge graph from the database schema."""

    def build(
        self,
        schema: DatabaseSchema,
        inferred_relationships: list[RelationshipInfo] | None = None,
        tenant_id: str | None = None,
    ) -> KnowledgeGraph:
        """
        Build a business knowledge graph from the discovered schema.
        
        Converts raw SQL tables into business concepts, classifies them
        into categories, and identifies primary business entities.
        """
        logger.info("Building knowledge graph", tenant_id=tenant_id)

        all_relationships = list(schema.relationships)
        if inferred_relationships:
            all_relationships.extend(inferred_relationships)

        concepts: list[BusinessConcept] = []

        # Process tables
        for table in schema.tables:
            concept = self._table_to_concept(table, all_relationships)
            concepts.append(concept)

        # Process views (often represent reporting/aggregate concepts)
        for view in schema.views:
            concept = self._table_to_concept(view, all_relationships)
            concept.category = self._classify_category(view.name) or "reporting"
            concepts.append(concept)

        # Link related concepts
        self._link_related_concepts(concepts, all_relationships)

        graph = KnowledgeGraph(
            concepts=concepts,
            relationships=all_relationships,
            built_at=datetime.utcnow(),
            tenant_id=tenant_id,
        )

        logger.info(
            "Knowledge graph built",
            concepts=len(concepts),
            relationships=len(all_relationships),
            primary_entities=sum(1 for c in concepts if self._is_primary_entity(c.sql_name)),
            tenant_id=tenant_id,
        )

        return graph

    def _table_to_concept(
        self, table: TableInfo, relationships: list[RelationshipInfo]
    ) -> BusinessConcept:
        """Convert a table/view to a business concept."""
        business_name = self._generate_business_name(table.name)
        category = self._classify_category(table.name) or "other"
        description = self._generate_description(table, relationships)

        key_columns = [
            col.name for col in table.columns
            if col.is_primary_key or col.is_foreign_key
        ]

        return BusinessConcept(
            sql_name=table.name,
            business_name=business_name,
            description=description,
            category=category,
            key_columns=key_columns,
        )

    def _generate_business_name(self, table_name: str) -> str:
        """Generate a human-readable business name from a SQL table name."""
        name = table_name

        # Remove common prefixes
        prefixes = ["tbl", "tbl_", "t_", "tb_", "vw_", "vw", "fn_"]
        for prefix in prefixes:
            if name.lower().startswith(prefix):
                name = name[len(prefix):]
                break

        # Convert CamelCase to spaces
        import re
        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)

        # Convert underscores to spaces
        name = name.replace("_", " ")

        # Title case
        name = name.strip().title()

        return name

    def _classify_category(self, table_name: str) -> str | None:
        """Classify a table into a business category."""
        name_lower = table_name.lower()

        for category, keywords in CATEGORY_RULES.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return category

        return None

    def _is_primary_entity(self, table_name: str) -> bool:
        """Check if a table represents a primary business entity."""
        name_lower = table_name.lower()
        for keyword in PRIMARY_ENTITY_KEYWORDS:
            if keyword in name_lower:
                return True
        return False

    def _generate_description(
        self, table: TableInfo, relationships: list[RelationshipInfo]
    ) -> str:
        """Generate a business description for a table."""
        parts = []

        # Base description from table type
        if table.table_type == "VIEW":
            parts.append(f"Reporting view")
        else:
            parts.append(f"Business entity")

        # Add column count
        parts.append(f"with {len(table.columns)} attributes")

        # Add row count if available
        if table.row_count:
            parts.append(f"containing {table.row_count:,} records")

        # Add relationship info
        related_tables = set()
        for rel in relationships:
            if rel.source_table == table.name:
                related_tables.add(rel.target_table)
            elif rel.target_table == table.name:
                related_tables.add(rel.source_table)

        if related_tables:
            parts.append(f"linked to {len(related_tables)} other entities")

        return " ".join(parts) + "."

    def _link_related_concepts(
        self, concepts: list[BusinessConcept], relationships: list[RelationshipInfo]
    ) -> None:
        """Populate the related_concepts field based on relationships."""
        concept_lookup = {c.sql_name: c for c in concepts}

        for rel in relationships:
            source = concept_lookup.get(rel.source_table)
            target = concept_lookup.get(rel.target_table)

            if source and target:
                if target.sql_name not in source.related_concepts:
                    source.related_concepts.append(target.sql_name)
                if source.sql_name not in target.related_concepts:
                    target.related_concepts.append(source.sql_name)
