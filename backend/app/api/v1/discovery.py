"""
AI Freight Copilot — Database Discovery API.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.dependencies import get_container

router = APIRouter(prefix="/discovery", tags=["discovery"])


class DiscoveryResponse(BaseModel):
    tables_count: int
    views_count: int
    procedures_count: int
    relationships_count: int
    concepts_count: int
    schema: dict | None = None
    knowledge_graph: dict | None = None


@router.post("/run", response_model=DiscoveryResponse)
async def run_discovery() -> DiscoveryResponse:
    """
    Trigger full database discovery.
    
    Inspects the ERP database schema, infers relationships,
    and builds the business knowledge graph.
    """
    container = get_container()

    try:
        # Step 1: Inspect schema
        schema = await container.schema_inspector.inspect_full_schema()

        # Step 2: Infer additional relationships
        inferred = container.relationship_inferrer.infer_relationships(schema)
        schema.relationships.extend(inferred)

        # Step 3: Build knowledge graph
        graph = container.knowledge_graph_builder.build(schema, inferred)
        container.knowledge_graph = graph

        return DiscoveryResponse(
            tables_count=len(schema.tables),
            views_count=len(schema.views),
            procedures_count=len(schema.stored_procedures),
            relationships_count=len(schema.relationships),
            concepts_count=len(graph.concepts),
            schema=schema.model_dump(),
            knowledge_graph=graph.model_dump(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


@router.get("/schema")
async def get_schema() -> dict:
    """Get the current discovered schema."""
    container = get_container()
    if not container.knowledge_graph:
        raise HTTPException(status_code=404, detail="No schema discovered yet. Run /discovery/run first.")

    return container.knowledge_graph.model_dump()


@router.get("/concepts")
async def get_business_concepts() -> list[dict]:
    """Get all business concepts mapped from the database."""
    container = get_container()
    if not container.knowledge_graph:
        raise HTTPException(status_code=404, detail="No schema discovered yet.")

    return [c.model_dump() for c in container.knowledge_graph.concepts]
