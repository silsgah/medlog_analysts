"""
AI Freight Copilot — Domain Entities.

Core business domain models following DDD principles.
These represent the primary business concepts the system reasons about.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enumerations ─────────────────────────────────────────────────────────────


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT = "insufficient"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ReportType(str, Enum):
    DAILY_EXECUTIVE = "daily_executive"
    WEEKLY_BUSINESS = "weekly_business"
    MONTHLY_FINANCIAL = "monthly_financial"
    BRANCH_PERFORMANCE = "branch_performance"
    CUSTOMER_RISK = "customer_risk"
    CASH_FLOW_FORECAST = "cash_flow_forecast"
    RECEIVABLES = "receivables"
    EXPENSE_ANALYSIS = "expense_analysis"
    PROFITABILITY = "profitability"
    OPERATIONAL_KPI = "operational_kpi"


class AnomalyType(str, Enum):
    SUSPICIOUS_WITHDRAWAL = "suspicious_withdrawal"
    DUPLICATE_PAYMENT = "duplicate_payment"
    DUPLICATE_EXPENSE = "duplicate_expense"
    DELAYED_COLLECTION = "delayed_collection"
    UNUSUAL_FUEL_USAGE = "unusual_fuel_usage"
    REVENUE_DROP = "revenue_drop"
    EXPENSE_SPIKE = "expense_spike"
    INACTIVE_CUSTOMER = "inactive_customer"
    BRANCH_OUTLIER = "branch_outlier"
    PAYMENT_IRREGULARITY = "payment_irregularity"


class TrendDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


# ── Database Discovery Entities ──────────────────────────────────────────────


class ColumnInfo(BaseModel):
    """Represents a database column."""
    name: str
    data_type: str
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    max_length: int | None = None
    default_value: str | None = None
    references_table: str | None = None
    references_column: str | None = None
    business_name: str | None = None
    description: str | None = None


class TableInfo(BaseModel):
    """Represents a database table or view."""
    schema_name: str = "dbo"
    name: str
    table_type: str = "TABLE"  # TABLE, VIEW
    columns: list[ColumnInfo] = Field(default_factory=list)
    row_count: int | None = None
    business_name: str | None = None
    business_description: str | None = None
    is_primary_entity: bool = False


class StoredProcedureInfo(BaseModel):
    """Represents a stored procedure."""
    schema_name: str = "dbo"
    name: str
    parameters: list[dict[str, Any]] = Field(default_factory=list)
    description: str | None = None


class RelationshipInfo(BaseModel):
    """Represents a relationship between tables."""
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    relationship_type: str = "many-to-one"  # one-to-one, one-to-many, many-to-one, many-to-many
    is_inferred: bool = False
    confidence: float = 1.0


class DatabaseSchema(BaseModel):
    """Complete database schema representation."""
    tables: list[TableInfo] = Field(default_factory=list)
    views: list[TableInfo] = Field(default_factory=list)
    stored_procedures: list[StoredProcedureInfo] = Field(default_factory=list)
    relationships: list[RelationshipInfo] = Field(default_factory=list)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


# ── Business Knowledge Entities ──────────────────────────────────────────────


class BusinessConcept(BaseModel):
    """Maps a SQL table/view to a business concept."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sql_name: str
    business_name: str
    description: str
    category: str  # e.g., "finance", "operations", "customers"
    key_columns: list[str] = Field(default_factory=list)
    related_concepts: list[str] = Field(default_factory=list)


class KnowledgeGraph(BaseModel):
    """Business knowledge graph built from database schema."""
    concepts: list[BusinessConcept] = Field(default_factory=list)
    relationships: list[RelationshipInfo] = Field(default_factory=list)
    built_at: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: str | None = None


# ── Financial Intelligence Entities ──────────────────────────────────────────


class MetricValue(BaseModel):
    """A single metric measurement."""
    name: str
    value: float
    unit: str = ""  # e.g., "GHS", "%", "days"
    period: str = ""  # e.g., "2024-01", "2024-W01"
    trend: TrendDirection = TrendDirection.STABLE
    change_percent: float | None = None
    previous_value: float | None = None


class FinancialSnapshot(BaseModel):
    """Point-in-time financial state."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    period: str = ""
    revenue: MetricValue | None = None
    gross_profit: MetricValue | None = None
    net_profit: MetricValue | None = None
    cash_flow: MetricValue | None = None
    operating_margin: MetricValue | None = None
    collection_rate: MetricValue | None = None
    outstanding_receivables: MetricValue | None = None
    avg_payment_delay: MetricValue | None = None
    expense_ratio: MetricValue | None = None
    withdrawal_frequency: MetricValue | None = None
    branch_profitability: dict[str, MetricValue] = Field(default_factory=dict)
    customer_lifetime_value: dict[str, MetricValue] = Field(default_factory=dict)


class BusinessHealthScore(BaseModel):
    """Composite business health score."""
    score: int = Field(ge=0, le=100)
    components: dict[str, float] = Field(default_factory=dict)
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Anomaly Detection Entities ───────────────────────────────────────────────


class Anomaly(BaseModel):
    """A detected anomaly in business data."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    anomaly_type: AnomalyType
    severity: AlertSeverity
    metric_name: str
    current_value: float
    expected_value: float
    deviation: float
    detection_method: str  # e.g., "isolation_forest", "z_score"
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    details: dict[str, Any] = Field(default_factory=dict)
    related_records: list[dict[str, Any]] = Field(default_factory=list)


# ── Executive Reasoning Entities ─────────────────────────────────────────────


class Evidence(BaseModel):
    """Evidence supporting a finding."""
    description: str
    sql_query: str | None = None
    data_points: list[dict[str, Any]] = Field(default_factory=list)
    source_table: str | None = None
    metric_values: list[MetricValue] = Field(default_factory=list)


class Insight(BaseModel):
    """A structured executive insight following the reasoning template."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    finding: str
    confidence: ConfidenceLevel
    evidence: list[Evidence] = Field(default_factory=list)
    business_impact: str
    recommended_actions: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    source_query: str | None = None  # Original user question if from chat


class ExecutiveReport(BaseModel):
    """A complete executive report."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: ReportType
    title: str
    period: str
    health_score: BusinessHealthScore | None = None
    financial_snapshot: FinancialSnapshot | None = None
    insights: list[Insight] = Field(default_factory=list)
    anomalies: list[Anomaly] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: str | None = None


# ── Alert Entities ───────────────────────────────────────────────────────────


class Alert(BaseModel):
    """A business alert requiring management attention."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    title: str
    description: str
    insight: Insight | None = None
    anomaly: Anomaly | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    tenant_id: str | None = None


# ── Chat / Conversational AI Entities ────────────────────────────────────────


class ChatMessage(BaseModel):
    """A message in a chat conversation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # "user", "assistant", "system"
    content: str
    insight: Insight | None = None
    sql_queries: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatConversation(BaseModel):
    """A chat conversation session."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[ChatMessage] = Field(default_factory=list)
    tenant_id: str | None = None
    user_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Multi-Tenant Entities ───────────────────────────────────────────────────


class Tenant(BaseModel):
    """A tenant (company) in the multi-tenant system."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str
    database_config: dict[str, Any] = Field(default_factory=dict)
    ai_config: dict[str, Any] = Field(default_factory=dict)
    report_config: dict[str, Any] = Field(default_factory=dict)
    alert_config: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TenantUser(BaseModel):
    """A user belonging to a tenant."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    email: str
    name: str
    role: str = "viewer"  # admin, analyst, viewer
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
