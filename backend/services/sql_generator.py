import re
import logging

from services.llm_service import LLMService
from services.rag_service import RAGService, RAGContext
from services.schema_inspector import SchemaInspector

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a SQL expert for PostgreSQL. Given a database schema, business glossary, and example queries, generate a valid SQL query that answers the user's question.

Rules:
- Only use tables and columns present in <schema>
- Only generate SELECT statements (never INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE)
- Output ONLY the SQL query, no explanation or markdown formatting
- Use readable aliases
- Use LIMIT when appropriate to avoid huge result sets
"""


class SQLGenerator:
    def __init__(
        self,
        llm_service: LLMService,
        rag_service: RAGService,
        schema_inspector: SchemaInspector,
    ):
        self.llm = llm_service
        self.rag = rag_service
        self.schema_inspector = schema_inspector

    async def generate(self, question: str) -> tuple[str, list[str]]:
        # 1. Retrieve relevant context via RAG
        rag_context = await self.rag.retrieve_context(question)

        # 2. Get DDL for relevant tables (or all if RAG returned nothing)
        table_names = rag_context.relevant_tables or None
        schema_ddl = self.schema_inspector.get_tables_as_ddl(table_names)

        # 3. Build prompt
        user_prompt = self._build_prompt(question, schema_ddl, rag_context)

        # 4. Call LLM
        raw_response = await self.llm.chat(SYSTEM_PROMPT, user_prompt)

        # 5. Extract and validate SQL
        sql = self._extract_sql(raw_response)
        self._validate_sql(sql)

        return sql, rag_context.relevant_tables

    def _build_prompt(self, question: str, schema_ddl: str, ctx: RAGContext) -> str:
        parts = [f"<schema>\n{schema_ddl}\n</schema>"]

        if ctx.glossary_terms:
            glossary_text = "\n".join(f"- {t}" for t in ctx.glossary_terms)
            parts.append(f"<glossary>\n{glossary_text}\n</glossary>")

        if ctx.few_shot_examples:
            examples_text = "\n".join(f"- {e}" for e in ctx.few_shot_examples)
            parts.append(f"<examples>\n{examples_text}\n</examples>")

        parts.append(f"<question>\n{question}\n</question>")
        parts.append("Generate the SQL query:")

        return "\n\n".join(parts)

    def _extract_sql(self, response: str) -> str:
        # Try to extract from code block
        match = re.search(r"```(?:sql)?\s*\n?(.*?)\n?```", response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # Otherwise treat entire response as SQL
        return response.strip().rstrip(";") + ";"

    def _validate_sql(self, sql: str) -> None:
        sql_upper = sql.upper().strip()
        forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"]
        for keyword in forbidden:
            # Match keyword as a whole word at statement level
            if re.search(rf'\b{keyword}\b', sql_upper):
                raise ValueError(f"SQL contains forbidden keyword: {keyword}")
