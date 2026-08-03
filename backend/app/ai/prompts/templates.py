"""
AI Freight Copilot — Prompt Templates.

All prompt templates used across the system for AI interactions.
Each template follows the executive reasoning structure:
Finding → Confidence → Evidence → Business Impact → Recommended Actions.
"""

from __future__ import annotations


# ── System Prompts ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an AI Executive Copilot for a freight and logistics company.
Your role is to analyze business data and provide evidence-backed executive intelligence.

CRITICAL RULES:
1. NEVER invent or hallucinate facts. Every statement must be traceable to actual data.
2. If evidence is insufficient, explicitly state: "Insufficient evidence."
3. Always quantify findings with actual numbers from the data.
4. Every insight must follow this structure:
   - Finding: What happened
   - Confidence: High/Medium/Low/Insufficient
   - Evidence: Supporting data points and SQL queries
   - Business Impact: What this means for the business
   - Recommended Actions: What management should do next

You reason using BUSINESS CONCEPTS, not raw SQL table names.
You are analytical, precise, and action-oriented."""


# ── Database Discovery Prompts ───────────────────────────────────────────────

SCHEMA_ANALYSIS_PROMPT = """Analyze the following database schema and provide a business knowledge mapping.

DATABASE SCHEMA:
{schema_json}

For each table/view, provide:
1. A clear business name (e.g., "tblReceipt" → "Customer Payments")
2. A brief business description
3. The business category (finance, operations, customers, hr, audit, master)
4. Whether it's a primary business entity
5. Key business relationships

Return your analysis as a JSON object with this structure:
{{
    "mappings": [
        {{
            "sql_name": "table_name",
            "business_name": "Human Readable Name",
            "description": "Brief business description",
            "category": "category",
            "is_primary_entity": true/false,
            "key_relationships": ["related_table_1", "related_table_2"]
        }}
    ],
    "summary": "Brief overview of the business domain"
}}"""


# ── Conversational AI Prompts ────────────────────────────────────────────────

CHAT_SYSTEM_PROMPT = """You are an AI Executive Copilot for {company_name}, a freight and logistics company.

AVAILABLE BUSINESS DATA:
{schema_context}

BUSINESS CONCEPTS:
{business_concepts}

When answering questions:
1. Generate safe, read-only SQL queries to retrieve data
2. Analyze the results to form insights
3. Structure every response with: Finding, Confidence, Evidence, Business Impact, Recommended Actions
4. Reference specific numbers and data points
5. If data is insufficient, say so explicitly

IMPORTANT: Only generate SELECT queries. Never generate INSERT, UPDATE, DELETE, or any DDL statements."""


QUERY_GENERATION_PROMPT = """Based on the user's question, generate a SQL Server query to retrieve the relevant data.

USER QUESTION: {question}

AVAILABLE TABLES AND THEIR BUSINESS MEANINGS:
{table_context}

RULES:
1. Generate only SELECT queries — no modifications allowed
2. Use TOP clause to limit results (max 100 rows)
3. Use appropriate JOINs based on relationships
4. Include date filters when the question implies a time range
5. Use aggregations (SUM, COUNT, AVG) when appropriate
6. Alias columns with business-friendly names

Return ONLY the SQL query, nothing else."""


ANALYSIS_PROMPT = """Analyze the following data to answer the user's question.

USER QUESTION: {question}

DATA RETRIEVED:
{data_json}

SQL QUERY USED:
{sql_query}

Provide your analysis in this EXACT JSON structure:
{{
    "finding": "Clear statement of what the data shows",
    "confidence": "high|medium|low|insufficient",
    "evidence": [
        {{
            "description": "Specific data point or observation",
            "value": "The actual value/number"
        }}
    ],
    "business_impact": "What this means for the business",
    "recommended_actions": [
        "Specific action 1",
        "Specific action 2"
    ]
}}"""


# ── Report Generation Prompts ────────────────────────────────────────────────

DAILY_REPORT_PROMPT = """Generate a Daily Executive Intelligence Report for {company_name}.

Date: {report_date}

FINANCIAL METRICS:
{financial_data}

ANOMALIES DETECTED:
{anomalies_data}

ALERTS:
{alerts_data}

Generate a comprehensive executive report covering:
1. Business Health Score (0-100)
2. Key Financial Metrics with trends (↑/↓/→)
3. Top 5 Alerts ranked by severity
4. Recommended Actions prioritized by impact

Format as a structured JSON:
{{
    "health_score": 0-100,
    "health_components": {{
        "revenue": 0-100,
        "cash_flow": 0-100,
        "collections": 0-100,
        "expenses": 0-100,
        "operations": 0-100
    }},
    "executive_summary": "Brief 2-3 sentence overview",
    "key_metrics": [
        {{
            "name": "Revenue",
            "value": "GHS X",
            "trend": "up|down|stable",
            "change_percent": X
        }}
    ],
    "top_alerts": [
        {{
            "severity": "critical|high|medium",
            "message": "Alert description",
            "impact": "Business impact"
        }}
    ],
    "recommended_actions": [
        {{
            "priority": 1,
            "action": "What to do",
            "reason": "Why"
        }}
    ]
}}"""


ANOMALY_EXPLANATION_PROMPT = """Explain the following anomaly in business terms.

ANOMALY DETAILS:
- Type: {anomaly_type}
- Metric: {metric_name}
- Current Value: {current_value}
- Expected Value: {expected_value}
- Deviation: {deviation}
- Detection Method: {detection_method}

RELATED DATA:
{related_data}

Provide an explanation following the executive reasoning template:
1. Finding: What happened in plain business language
2. Confidence: How confident are you in this finding
3. Evidence: What data supports this
4. Business Impact: What this means for operations and finances
5. Recommended Actions: What management should do"""


# ── Email Templates ──────────────────────────────────────────────────────────

EMAIL_REPORT_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
    .container {{ max-width: 700px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 20px rgba(0,0,0,0.08); }}
    .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: #fff; padding: 30px; text-align: center; }}
    .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
    .header .date {{ color: #a8b2d1; font-size: 14px; margin-top: 8px; }}
    .health-score {{ text-align: center; padding: 30px; background: #fafbfc; }}
    .health-score .score {{ font-size: 64px; font-weight: 700; color: {score_color}; }}
    .health-score .label {{ font-size: 14px; color: #666; text-transform: uppercase; letter-spacing: 1px; }}
    .metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: #eee; }}
    .metric {{ background: #fff; padding: 20px; text-align: center; }}
    .metric .value {{ font-size: 24px; font-weight: 600; color: #1a1a2e; }}
    .metric .name {{ font-size: 12px; color: #888; text-transform: uppercase; margin-bottom: 4px; }}
    .metric .trend {{ font-size: 14px; }}
    .trend-up {{ color: #10b981; }}
    .trend-down {{ color: #ef4444; }}
    .trend-stable {{ color: #6b7280; }}
    .section {{ padding: 24px 30px; }}
    .section h2 {{ font-size: 18px; color: #1a1a2e; margin: 0 0 16px 0; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb; }}
    .alert {{ padding: 12px 16px; margin: 8px 0; border-radius: 8px; font-size: 14px; }}
    .alert-critical {{ background: #fef2f2; border-left: 4px solid #ef4444; }}
    .alert-high {{ background: #fff7ed; border-left: 4px solid #f59e0b; }}
    .alert-medium {{ background: #eff6ff; border-left: 4px solid #3b82f6; }}
    .action {{ padding: 10px 16px; margin: 6px 0; background: #f0fdf4; border-radius: 8px; font-size: 14px; border-left: 4px solid #10b981; }}
    .action .number {{ font-weight: 700; color: #059669; margin-right: 8px; }}
    .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #9ca3af; background: #fafbfc; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📊 Daily Executive Intelligence</h1>
        <div class="date">{report_date}</div>
    </div>
    
    <div class="health-score">
        <div class="label">Business Health Score</div>
        <div class="score">{health_score}</div>
    </div>
    
    <div class="metrics">
        {metrics_html}
    </div>
    
    <div class="section">
        <h2>🚨 Top Alerts</h2>
        {alerts_html}
    </div>
    
    <div class="section">
        <h2>✅ Recommended Actions</h2>
        {actions_html}
    </div>
    
    <div class="footer">
        Generated by AI Freight Copilot • {timestamp}
    </div>
</div>
</body>
</html>
"""
