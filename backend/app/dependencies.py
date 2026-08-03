"""
AI Freight Copilot — Dependency Injection.

Central dependency container providing all services to API routes.
"""

from __future__ import annotations

from functools import lru_cache

import structlog

from app.ai.llm_router import LLMRouter
from app.core.alerts.engine import AlertEngine
from app.core.anomaly.detector import AnomalyDetector
from app.core.discovery.inspector import SchemaInspector
from app.core.discovery.knowledge_graph import KnowledgeGraphBuilder
from app.core.discovery.relationship_inferrer import RelationshipInferrer
from app.core.financial.calculator import FinancialCalculator
from app.core.reasoning.engine import ReasoningEngine
from app.domain.entities import KnowledgeGraph
from app.infrastructure.database import DatabaseManager, get_database_manager
from app.services.chat_service import ChatService
from app.services.email_service import EmailService
from app.services.report_service import ReportService

logger = structlog.get_logger(__name__)


class ServiceContainer:
    """Central dependency injection container."""

    def __init__(self) -> None:
        self._db_manager: DatabaseManager | None = None
        self._llm_router: LLMRouter | None = None
        self._email_service: EmailService | None = None
        self._schema_inspector: SchemaInspector | None = None
        self._relationship_inferrer: RelationshipInferrer | None = None
        self._knowledge_graph_builder: KnowledgeGraphBuilder | None = None
        self._financial_calculator: FinancialCalculator | None = None
        self._anomaly_detector: AnomalyDetector | None = None
        self._reasoning_engine: ReasoningEngine | None = None
        self._alert_engine: AlertEngine | None = None
        self._chat_service: ChatService | None = None
        self._report_service: ReportService | None = None
        self._knowledge_graph: KnowledgeGraph | None = None

    async def initialize(self) -> None:
        """Initialize all services."""
        logger.info("Initializing service container")

        # Database
        self._db_manager = get_database_manager()
        await self._db_manager.initialize()

        # AI
        self._llm_router = LLMRouter()
        self._llm_router.initialize()

        # Email
        self._email_service = EmailService()
        self._email_service.initialize()

        # Core services
        self._schema_inspector = SchemaInspector(self._db_manager)
        self._relationship_inferrer = RelationshipInferrer()
        self._knowledge_graph_builder = KnowledgeGraphBuilder()
        self._financial_calculator = FinancialCalculator(self._db_manager)
        self._anomaly_detector = AnomalyDetector(self._db_manager)
        self._reasoning_engine = ReasoningEngine(self._llm_router)
        self._alert_engine = AlertEngine()

        # Application services
        self._chat_service = ChatService(
            db_manager=self._db_manager,
            llm_router=self._llm_router,
            reasoning_engine=self._reasoning_engine,
        )
        self._report_service = ReportService(
            financial_calculator=self._financial_calculator,
            anomaly_detector=self._anomaly_detector,
            alert_engine=self._alert_engine,
            llm_router=self._llm_router,
            email_service=self._email_service,
        )

        logger.info("Service container initialized")

    async def shutdown(self) -> None:
        """Shutdown all services."""
        if self._db_manager:
            await self._db_manager.shutdown()
        logger.info("Service container shut down")

    # ── Accessors ────────────────────────────────────────────────────────

    @property
    def db_manager(self) -> DatabaseManager:
        assert self._db_manager, "Service container not initialized"
        return self._db_manager

    @property
    def llm_router(self) -> LLMRouter:
        assert self._llm_router, "Service container not initialized"
        return self._llm_router

    @property
    def schema_inspector(self) -> SchemaInspector:
        assert self._schema_inspector, "Service container not initialized"
        return self._schema_inspector

    @property
    def relationship_inferrer(self) -> RelationshipInferrer:
        assert self._relationship_inferrer, "Service container not initialized"
        return self._relationship_inferrer

    @property
    def knowledge_graph_builder(self) -> KnowledgeGraphBuilder:
        assert self._knowledge_graph_builder, "Service container not initialized"
        return self._knowledge_graph_builder

    @property
    def financial_calculator(self) -> FinancialCalculator:
        assert self._financial_calculator, "Service container not initialized"
        return self._financial_calculator

    @property
    def anomaly_detector(self) -> AnomalyDetector:
        assert self._anomaly_detector, "Service container not initialized"
        return self._anomaly_detector

    @property
    def reasoning_engine(self) -> ReasoningEngine:
        assert self._reasoning_engine, "Service container not initialized"
        return self._reasoning_engine

    @property
    def alert_engine(self) -> AlertEngine:
        assert self._alert_engine, "Service container not initialized"
        return self._alert_engine

    @property
    def chat_service(self) -> ChatService:
        assert self._chat_service, "Service container not initialized"
        return self._chat_service

    @property
    def report_service(self) -> ReportService:
        assert self._report_service, "Service container not initialized"
        return self._report_service

    @property
    def knowledge_graph(self) -> KnowledgeGraph | None:
        return self._knowledge_graph

    @knowledge_graph.setter
    def knowledge_graph(self, graph: KnowledgeGraph) -> None:
        self._knowledge_graph = graph
        if self._chat_service:
            self._chat_service.update_knowledge_graph(graph)


# Module-level singleton
_container: ServiceContainer | None = None


def get_container() -> ServiceContainer:
    """Get the service container singleton."""
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container
