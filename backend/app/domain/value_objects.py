"""
AI Freight Copilot — Domain Value Objects.

Immutable value objects used across the domain layer.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DateRange(BaseModel):
    """Represents a date range for queries and reports."""
    start: str  # ISO date string
    end: str    # ISO date string
    label: str = ""  # e.g., "January 2024", "Q1 2024"

    class Config:
        frozen = True


class Money(BaseModel):
    """Represents a monetary value with currency."""
    amount: float
    currency: str = "GHS"

    class Config:
        frozen = True

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:,.2f}"


class Percentage(BaseModel):
    """Represents a percentage value."""
    value: float
    decimal_places: int = 1

    class Config:
        frozen = True

    def __str__(self) -> str:
        return f"{self.value:.{self.decimal_places}f}%"


class ThresholdRule(BaseModel):
    """Defines a threshold for alert triggering."""
    metric_name: str
    operator: str  # "gt", "lt", "gte", "lte", "eq", "pct_change_gt", "pct_change_lt"
    value: float
    window_days: int = 30
    description: str = ""

    class Config:
        frozen = True

    def evaluate(self, current_value: float, previous_value: float | None = None) -> bool:
        """Evaluate whether the threshold has been breached."""
        if self.operator == "gt":
            return current_value > self.value
        elif self.operator == "lt":
            return current_value < self.value
        elif self.operator == "gte":
            return current_value >= self.value
        elif self.operator == "lte":
            return current_value <= self.value
        elif self.operator == "eq":
            return current_value == self.value
        elif self.operator in ("pct_change_gt", "pct_change_lt") and previous_value is not None:
            if previous_value == 0:
                return False
            pct_change = ((current_value - previous_value) / abs(previous_value)) * 100
            if self.operator == "pct_change_gt":
                return pct_change > self.value
            return pct_change < -self.value
        return False


class QueryContext(BaseModel):
    """Context passed to AI for generating SQL and analysis."""
    tenant_id: str | None = None
    available_tables: list[str] = Field(default_factory=list)
    business_concepts: dict[str, str] = Field(default_factory=dict)  # sql_name -> business_name
    schema_summary: str = ""
    user_question: str = ""
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    time_range: DateRange | None = None

    class Config:
        frozen = True


class SQLResult(BaseModel):
    """Result of executing a SQL query."""
    query: str
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    error: str | None = None
    is_truncated: bool = False

    class Config:
        frozen = True
