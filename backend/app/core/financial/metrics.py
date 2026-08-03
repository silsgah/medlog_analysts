"""
AI Freight Copilot — Financial Metric Definitions.

Defines all financial KPIs, their SQL calculation queries,
and business interpretation rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MetricCategory(str, Enum):
    REVENUE = "revenue"
    PROFITABILITY = "profitability"
    CASH_FLOW = "cash_flow"
    COLLECTIONS = "collections"
    EXPENSES = "expenses"
    OPERATIONS = "operations"
    CUSTOMER = "customer"


@dataclass
class MetricDefinition:
    """Definition of a financial metric with its SQL query template."""
    name: str
    display_name: str
    category: MetricCategory
    unit: str  # "currency", "percent", "days", "count", "ratio"
    description: str
    query_template: str
    comparison_query_template: str = ""
    higher_is_better: bool = True
    warning_threshold: float | None = None
    critical_threshold: float | None = None
    health_weight: float = 0.0  # Weight in health score (0-1)

    def get_trend_query(self, periods: int = 12) -> str:
        """Get query for trend analysis over multiple periods."""
        return self.query_template  # Subclasses can override


# ── Standard Financial Metrics ───────────────────────────────────────────────

METRIC_DEFINITIONS: dict[str, MetricDefinition] = {
    "revenue": MetricDefinition(
        name="revenue",
        display_name="Revenue",
        category=MetricCategory.REVENUE,
        unit="currency",
        description="Total revenue from invoices in the period",
        query_template="""
            SELECT ISNULL(SUM(TotalAmount), 0) AS value
            FROM {invoice_table}
            WHERE {date_column} BETWEEN :start_date AND :end_date
        """,
        comparison_query_template="""
            SELECT ISNULL(SUM(TotalAmount), 0) AS value
            FROM {invoice_table}
            WHERE {date_column} BETWEEN :prev_start_date AND :prev_end_date
        """,
        higher_is_better=True,
        health_weight=0.20,
    ),
    "gross_profit": MetricDefinition(
        name="gross_profit",
        display_name="Gross Profit",
        category=MetricCategory.PROFITABILITY,
        unit="currency",
        description="Revenue minus direct costs",
        query_template="""
            SELECT ISNULL(SUM(TotalAmount), 0) - ISNULL(
                (SELECT SUM(Amount) FROM {expense_table} 
                 WHERE {expense_date_column} BETWEEN :start_date AND :end_date
                 AND Category IN ('Direct Cost', 'COGS', 'Freight Cost')), 0
            ) AS value
            FROM {invoice_table}
            WHERE {date_column} BETWEEN :start_date AND :end_date
        """,
        higher_is_better=True,
        health_weight=0.15,
    ),
    "net_profit": MetricDefinition(
        name="net_profit",
        display_name="Net Profit",
        category=MetricCategory.PROFITABILITY,
        unit="currency",
        description="Revenue minus all expenses",
        query_template="""
            SELECT 
                ISNULL((SELECT SUM(TotalAmount) FROM {invoice_table} 
                        WHERE {date_column} BETWEEN :start_date AND :end_date), 0)
                - ISNULL((SELECT SUM(Amount) FROM {expense_table} 
                          WHERE {expense_date_column} BETWEEN :start_date AND :end_date), 0)
            AS value
        """,
        higher_is_better=True,
        health_weight=0.15,
    ),
    "cash_flow": MetricDefinition(
        name="cash_flow",
        display_name="Cash Flow",
        category=MetricCategory.CASH_FLOW,
        unit="currency",
        description="Cash received minus cash paid out",
        query_template="""
            SELECT 
                ISNULL((SELECT SUM(Amount) FROM {receipt_table} 
                        WHERE {receipt_date_column} BETWEEN :start_date AND :end_date), 0)
                - ISNULL((SELECT SUM(Amount) FROM {withdrawal_table} 
                          WHERE {withdrawal_date_column} BETWEEN :start_date AND :end_date), 0)
            AS value
        """,
        higher_is_better=True,
        critical_threshold=0,
        health_weight=0.15,
    ),
    "operating_margin": MetricDefinition(
        name="operating_margin",
        display_name="Operating Margin",
        category=MetricCategory.PROFITABILITY,
        unit="percent",
        description="Operating profit as percentage of revenue",
        query_template="""
            SELECT CASE 
                WHEN ISNULL(SUM(i.TotalAmount), 0) = 0 THEN 0
                ELSE (
                    (ISNULL(SUM(i.TotalAmount), 0) - ISNULL((
                        SELECT SUM(Amount) FROM {expense_table} 
                        WHERE {expense_date_column} BETWEEN :start_date AND :end_date
                    ), 0)) * 100.0 / ISNULL(SUM(i.TotalAmount), 1)
                )
            END AS value
            FROM {invoice_table} i
            WHERE i.{date_column} BETWEEN :start_date AND :end_date
        """,
        higher_is_better=True,
        warning_threshold=10.0,
        critical_threshold=5.0,
        health_weight=0.10,
    ),
    "collection_rate": MetricDefinition(
        name="collection_rate",
        display_name="Collection Rate",
        category=MetricCategory.COLLECTIONS,
        unit="percent",
        description="Percentage of invoiced amount collected",
        query_template="""
            SELECT CASE 
                WHEN ISNULL((SELECT SUM(TotalAmount) FROM {invoice_table} 
                             WHERE {date_column} BETWEEN :start_date AND :end_date), 0) = 0 THEN 0
                ELSE (
                    ISNULL((SELECT SUM(Amount) FROM {receipt_table} 
                            WHERE {receipt_date_column} BETWEEN :start_date AND :end_date), 0)
                    * 100.0 / 
                    ISNULL((SELECT SUM(TotalAmount) FROM {invoice_table} 
                            WHERE {date_column} BETWEEN :start_date AND :end_date), 1)
                )
            END AS value
        """,
        higher_is_better=True,
        warning_threshold=70.0,
        critical_threshold=50.0,
        health_weight=0.10,
    ),
    "outstanding_receivables": MetricDefinition(
        name="outstanding_receivables",
        display_name="Outstanding Receivables",
        category=MetricCategory.COLLECTIONS,
        unit="currency",
        description="Total amount owed by customers",
        query_template="""
            SELECT ISNULL(SUM(BalanceDue), 0) AS value
            FROM {invoice_table}
            WHERE BalanceDue > 0
        """,
        higher_is_better=False,
        health_weight=0.05,
    ),
    "avg_payment_delay": MetricDefinition(
        name="avg_payment_delay",
        display_name="Average Payment Delay",
        category=MetricCategory.COLLECTIONS,
        unit="days",
        description="Average days between invoice date and payment date",
        query_template="""
            SELECT ISNULL(AVG(DATEDIFF(day, i.{date_column}, r.{receipt_date_column})), 0) AS value
            FROM {invoice_table} i
            JOIN {receipt_table} r ON i.CustomerID = r.CustomerID
            WHERE r.{receipt_date_column} BETWEEN :start_date AND :end_date
        """,
        higher_is_better=False,
        warning_threshold=45,
        critical_threshold=90,
        health_weight=0.05,
    ),
    "expense_ratio": MetricDefinition(
        name="expense_ratio",
        display_name="Expense Ratio",
        category=MetricCategory.EXPENSES,
        unit="percent",
        description="Total expenses as percentage of revenue",
        query_template="""
            SELECT CASE 
                WHEN ISNULL((SELECT SUM(TotalAmount) FROM {invoice_table} 
                             WHERE {date_column} BETWEEN :start_date AND :end_date), 0) = 0 THEN 0
                ELSE (
                    ISNULL((SELECT SUM(Amount) FROM {expense_table} 
                            WHERE {expense_date_column} BETWEEN :start_date AND :end_date), 0)
                    * 100.0 / 
                    ISNULL((SELECT SUM(TotalAmount) FROM {invoice_table} 
                            WHERE {date_column} BETWEEN :start_date AND :end_date), 1)
                )
            END AS value
        """,
        higher_is_better=False,
        warning_threshold=85.0,
        critical_threshold=95.0,
        health_weight=0.05,
    ),
    "withdrawal_frequency": MetricDefinition(
        name="withdrawal_frequency",
        display_name="Withdrawal Frequency",
        category=MetricCategory.CASH_FLOW,
        unit="count",
        description="Number of bank withdrawals in the period",
        query_template="""
            SELECT COUNT(*) AS value
            FROM {withdrawal_table}
            WHERE {withdrawal_date_column} BETWEEN :start_date AND :end_date
        """,
        higher_is_better=False,
        health_weight=0.0,
    ),
}


# ── Table Mapping Configuration ──────────────────────────────────────────────
# These are default mappings that get overridden by database discovery

@dataclass
class TableMapping:
    """Maps business concepts to actual SQL table/column names."""
    invoice_table: str = "tblInvoice"
    date_column: str = "InvoiceDate"
    receipt_table: str = "tblReceipt"
    receipt_date_column: str = "ReceiptDate"
    expense_table: str = "tblExpense"
    expense_date_column: str = "ExpenseDate"
    withdrawal_table: str = "tblWithdrawal"
    withdrawal_date_column: str = "WithdrawalDate"
    customer_table: str = "tblCustomer"
    job_table: str = "tblJob"
    branch_table: str = "tblBranch"

    def apply_to_query(self, query_template: str) -> str:
        """Replace placeholders in a query template with actual table/column names."""
        replacements = {
            "{invoice_table}": self.invoice_table,
            "{date_column}": self.date_column,
            "{receipt_table}": self.receipt_table,
            "{receipt_date_column}": self.receipt_date_column,
            "{expense_table}": self.expense_table,
            "{expense_date_column}": self.expense_date_column,
            "{withdrawal_table}": self.withdrawal_table,
            "{withdrawal_date_column}": self.withdrawal_date_column,
            "{customer_table}": self.customer_table,
            "{job_table}": self.job_table,
            "{branch_table}": self.branch_table,
        }
        result = query_template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        return result
