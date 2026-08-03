"""
AI Freight Copilot — Chat Service.

Handles conversational AI interactions: parses user questions,
generates SQL, executes queries, and returns structured insights.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, AsyncIterator

import structlog

from app.ai.llm_router import LLMRouter
from app.ai.providers.base import Message, MessageRole
from app.ai.prompts.templates import CHAT_SYSTEM_PROMPT, QUERY_GENERATION_PROMPT, SYSTEM_PROMPT
from app.core.reasoning.engine import ReasoningEngine
from app.domain.entities import ChatConversation, ChatMessage, Insight, KnowledgeGraph
from app.infrastructure.database import DatabaseManager

logger = structlog.get_logger(__name__)


class ChatService:
    """
    Conversational AI service for executive Q&A.
    
    Translates natural language questions into SQL queries,
    executes them safely, and returns evidence-backed insights.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        llm_router: LLMRouter,
        reasoning_engine: ReasoningEngine,
        knowledge_graph: KnowledgeGraph | None = None,
    ) -> None:
        self._db = db_manager
        self._llm = llm_router
        self._reasoning = reasoning_engine
        self._knowledge_graph = knowledge_graph
        self._conversations: dict[str, ChatConversation] = {}

    def _build_schema_context(self) -> str:
        """Build schema context from knowledge graph for the AI."""
        if not self._knowledge_graph:
            return "No schema information available yet. Run database discovery first."

        lines = []
        for concept in self._knowledge_graph.concepts:
            lines.append(f"- {concept.sql_name} → {concept.business_name}: {concept.description}")
        return "\n".join(lines)

    def _build_business_concepts(self) -> str:
        """Build business concepts mapping."""
        if not self._knowledge_graph:
            return "No business concepts mapped yet."

        lines = []
        for concept in self._knowledge_graph.concepts:
            lines.append(f"- \"{concept.business_name}\" = SQL table `{concept.sql_name}` ({concept.category})")
        return "\n".join(lines)

    async def ask(
        self,
        question: str,
        conversation_id: str | None = None,
        tenant_id: str | None = None,
    ) -> ChatMessage:
        """
        Process a user question and return an evidence-backed response.
        
        Flow:
        1. Parse the question
        2. Generate a SQL query
        3. Execute the query (read-only)
        4. Analyze results through reasoning engine
        5. Return structured insight
        """
        logger.info("Processing chat question", question=question[:100])

        # Get or create conversation
        conversation = self._get_or_create_conversation(conversation_id, tenant_id)

        # Add user message
        user_msg = ChatMessage(role="user", content=question)
        conversation.messages.append(user_msg)

        try:
            # Step 1: Generate SQL query from natural language
            sql_query = await self._generate_sql(question, conversation)

            # Step 2: Execute query safely
            result = await self._db.execute_erp_query(
                sql_query, tenant_id=tenant_id, max_rows=100
            )

            # Step 3: Analyze through reasoning engine
            insight = await self._reasoning.analyze_query_result(question, result)

            # Step 4: Format response
            response_content = self._format_insight_response(insight)

            assistant_msg = ChatMessage(
                role="assistant",
                content=response_content,
                insight=insight,
                sql_queries=[sql_query],
            )
            conversation.messages.append(assistant_msg)
            conversation.updated_at = datetime.utcnow()

            return assistant_msg

        except PermissionError as e:
            error_msg = ChatMessage(
                role="assistant",
                content=f"⚠️ Safety check: {str(e)}\n\nI can only run read-only queries against the database.",
            )
            conversation.messages.append(error_msg)
            return error_msg

        except Exception as e:
            logger.error("Chat processing failed", error=str(e), exc_info=True)
            error_msg = ChatMessage(
                role="assistant",
                content=f"I encountered an error processing your question: {str(e)}\n\nPlease try rephrasing your question.",
            )
            conversation.messages.append(error_msg)
            return error_msg

    async def ask_stream(
        self,
        question: str,
        conversation_id: str | None = None,
        tenant_id: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream a response for the user question."""
        # For streaming, we generate SQL first, then stream the analysis
        try:
            sql_query = await self._generate_sql(question)
            result = await self._db.execute_erp_query(
                sql_query, tenant_id=tenant_id, max_rows=100
            )

            if result.error:
                yield f"⚠️ Query error: {result.error}"
                return

            # Stream the AI analysis
            data_preview = json.dumps(result.rows[:50], default=str, indent=2)
            messages = [
                Message(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT),
                Message(
                    role=MessageRole.USER,
                    content=f"Question: {question}\n\nData:\n{data_preview}\n\nSQL: {sql_query}\n\n"
                    f"Provide your analysis with Finding, Confidence, Evidence, Business Impact, and Recommended Actions.",
                ),
            ]

            yield f"\n📊 **SQL Query Used:**\n```sql\n{sql_query}\n```\n\n"
            yield f"📈 **Data Retrieved:** {len(result.rows)} rows\n\n"
            yield "---\n\n"

            async for chunk in self._llm.generate_stream(messages):
                yield chunk

        except Exception as e:
            yield f"\n⚠️ Error: {str(e)}"

    async def _generate_sql(
        self,
        question: str,
        conversation: ChatConversation | None = None,
    ) -> str:
        """Generate a SQL query from a natural language question."""
        table_context = self._build_schema_context()

        prompt = QUERY_GENERATION_PROMPT.format(
            question=question,
            table_context=table_context,
        )

        messages = [
            Message(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT),
            Message(role=MessageRole.USER, content=prompt),
        ]

        # Add conversation history for context
        if conversation and len(conversation.messages) > 1:
            history_context = "\n".join([
                f"{m.role}: {m.content[:200]}"
                for m in conversation.messages[-4:]  # Last 4 messages
            ])
            messages.insert(1, Message(
                role=MessageRole.USER,
                content=f"Conversation context:\n{history_context}",
            ))

        response = await self._llm.generate(messages, temperature=0.0)

        # Extract SQL from response (strip markdown code blocks if present)
        sql = response.content.strip()
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]

        return sql.strip()

    def _format_insight_response(self, insight: Insight) -> str:
        """Format an insight into a readable chat response."""
        parts = []

        parts.append(f"## 🔍 Finding\n{insight.finding}")
        parts.append(f"\n## 📊 Confidence\n**{insight.confidence.value.title()}**")

        if insight.evidence:
            parts.append("\n## 📋 Evidence")
            for i, ev in enumerate(insight.evidence, 1):
                parts.append(f"  {i}. {ev.description}")
                if ev.sql_query:
                    parts.append(f"     ```sql\n     {ev.sql_query}\n     ```")

        if insight.business_impact:
            parts.append(f"\n## 💼 Business Impact\n{insight.business_impact}")

        if insight.recommended_actions:
            parts.append("\n## ✅ Recommended Actions")
            for i, action in enumerate(insight.recommended_actions, 1):
                parts.append(f"  {i}. {action}")

        return "\n".join(parts)

    def _get_or_create_conversation(
        self, conversation_id: str | None, tenant_id: str | None
    ) -> ChatConversation:
        """Get an existing conversation or create a new one."""
        if conversation_id and conversation_id in self._conversations:
            return self._conversations[conversation_id]

        conv = ChatConversation(tenant_id=tenant_id)
        if conversation_id:
            conv.id = conversation_id

        self._conversations[conv.id] = conv
        return conv

    def get_conversation(self, conversation_id: str) -> ChatConversation | None:
        """Get a conversation by ID."""
        return self._conversations.get(conversation_id)

    def update_knowledge_graph(self, graph: KnowledgeGraph) -> None:
        """Update the knowledge graph used for context."""
        self._knowledge_graph = graph
        logger.info("Knowledge graph updated for chat service")
