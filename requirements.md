# AI Freight Operations & Financial Intelligence Copilot

## Objective

Build a production-ready AI-powered Operations and Financial Intelligence Copilot for freight and logistics companies.

The platform must NOT replace the existing freight ERP or accounting system.

Instead, it connects directly to the existing SQL Server database and becomes the intelligence layer sitting on top of operational data.

The objective is to automatically understand business operations, identify anomalies, explain financial performance, generate executive summaries, recommend corrective actions, and provide a conversational AI interface for management.

The system must be designed so it can later be generalized into a multi-tenant AI Business Intelligence platform for SMEs across different industries.

---

# Core Philosophy

We are NOT building another dashboard.

We are NOT building another chatbot.

We are building an AI Executive Copilot.

Every insight produced by the system must answer:

1. What happened?
2. Why did it happen?
3. What evidence supports this?
4. What should management do next?

No hallucinations.

Every recommendation must be traceable back to actual business data.

---

# Existing Environment

Existing freight platform

- ASP.NET MVC (.NET Framework)
- Microsoft SQL Server
- Existing reporting views
- Existing stored procedures
- Existing accounting module
- Existing customer module
- Existing shipment module
- Existing payment module

The AI platform MUST connect to the existing SQL Server database.

It must NEVER require replacing the ERP.

---

# Technology Stack

Backend

- Python 3.12
- FastAPI
- SQLAlchemy
- APScheduler
- Celery/Dramatiq
- Redis

AI

- OpenAI compatible API
- Local vLLM support
- Anthropic support
- Gemini support

Embeddings

- Qdrant

Email

- Resend

Frontend

- Next.js
- React
- Tailwind
- shadcn/ui

Deployment

Docker

Docker Compose

---

# Phase 1

## Automatic Database Discovery

After connecting to SQL Server the system should

- inspect every table
- inspect every view
- inspect every stored procedure
- infer relationships
- build a business knowledge graph
- identify primary entities

Examples

Customers

Invoices

Receipts

Payments

Expenses

Cash Book

Bank Withdrawals

Jobs

Containers

Shipments

Agents

Branches

Currencies

Taxes

Users

Audit Logs

---

# Business Knowledge Layer

Convert the SQL schema into business concepts.

Example

tblReceipt

↓

Customer Payments

tblWithdrawal

↓

Bank Withdrawals

tblExpense

↓

Operational Expenses

etc.

The AI should reason using business concepts instead of raw SQL table names.

---

# Daily Executive Intelligence Report

Every morning automatically generate an executive email.

Example

------------------------------------------------

Business Health Score

84 / 100

Revenue

↑ 8%

Cash Position

↓ 6%

Outstanding Receivables

GHS XXX

Bank Withdrawals

↑ 32%

Collection Rate

71%

Highest Risk Branch

Takoradi

Top Five Alerts

• Cash withdrawals unusually high.

• Customer ABC overdue by 94 days.

• Branch Kumasi has negative cash flow.

• Fuel expenses increased 19%.

• Invoice reconciliation mismatch detected.

Recommended Actions

1. Review withdrawals above threshold.

2. Contact top overdue customers.

3. Investigate Branch Kumasi.

------------------------------------------------

Email must be delivered automatically using Resend.

---

# Conversational AI

Management should ask

Why is revenue declining?

Which customers owe us the most?

Why are withdrawals increasing?

Show overdue invoices.

Compare this month with last month.

Predict next month's cash flow.

Which branch is least profitable?

Why is profit decreasing?

Which expenses are abnormal?

Every answer must include

Finding

Confidence

Evidence

Business Impact

Recommended Actions

SQL queries used

---

# Financial Intelligence

Automatically calculate

Revenue

Gross Profit

Net Profit

Cash Flow

Operating Margin

Collection Rate

Outstanding Receivables

Average Payment Delay

Expense Ratio

Withdrawal Frequency

Branch Profitability

Customer Lifetime Value

Revenue Trend

Cost Trend

Cash Trend

---

# AI Anomaly Detection

Implement

Isolation Forest

Rolling Statistics

Z-score

Moving Average

Seasonality Detection

Trend Change Detection

Pattern Drift

Detect

Suspicious Withdrawals

Duplicate Payments

Duplicate Expenses

Delayed Collections

Unusual Fuel Usage

Revenue Drops

Expense Spikes

Inactive Customers

Branch Outliers

Payment Irregularities

---

# Executive Reasoning Template

Every insight must follow this structure.

Finding

Confidence

Evidence

Business Impact

Recommended Actions

Example

Finding

Cash withdrawals increased by 41%.

Confidence

High

Evidence

112 withdrawals recorded this month.

Historical average is 79.

Only 38% have linked customer payments.

Business Impact

Possible cash leakage or delayed payment recording.

Recommended Actions

Review top ten withdrawals.

Verify customer payment postings.

Audit affected branches.

---

# Explainability

The AI must NEVER invent facts.

Every conclusion must be backed by

SQL

Business Rules

Aggregated Metrics

Historical Trends

If evidence is weak, explicitly state

"Insufficient evidence."

---

# Scheduled Reports

Daily Executive Report

Weekly Business Review

Monthly Financial Review

Branch Performance Report

Customer Risk Report

Cash Flow Forecast

Receivables Report

Expense Analysis

Profitability Analysis

Operational KPI Report

---

# Alert Engine

Notify management immediately when

Revenue drops sharply

Cash flow becomes negative

Large withdrawals occur

Collections fall below threshold

Expense spikes detected

Duplicate payments found

Invoices become overdue

Customer risk exceeds threshold

---

# Multi-Tenant Architecture

Although Phase 1 targets a freight company, the architecture must support multiple companies.

Each tenant has

Own database connection

Own KPIs

Own AI prompts

Own reports

Own users

Own scheduled emails

---

# Future Modules

Payroll Intelligence

Inventory Intelligence

School Analytics

Hospital Analytics

Construction Analytics

Manufacturing Analytics

Retail Analytics

NGO Analytics

---

# Coding Principles

Use Clean Architecture.

Use Domain-Driven Design.

Strong typing.

Repository pattern.

Async everywhere.

Configuration driven.

Well documented.

Unit tests.

Production-ready logging.

Observability.

Dockerized.

No hardcoded business logic.

Everything extensible.

---

# Ultimate Vision

Build the AI Executive Copilot for African businesses.

The platform should become the intelligence layer sitting on top of existing ERP systems, transforming operational and financial data into evidence-backed executive decisions using trustworthy AI rather than generic chatbot responses.