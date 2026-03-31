import logging
from dataclasses import dataclass, field

from services.embedding_service import EmbeddingService
from services.indexing_service import IndexingService

logger = logging.getLogger(__name__)


@dataclass
class RAGContext:
    relevant_tables: list[str] = field(default_factory=list)
    table_descriptions: list[str] = field(default_factory=list)
    glossary_terms: list[str] = field(default_factory=list)
    few_shot_examples: list[str] = field(default_factory=list)


class RAGService:
    def __init__(self, embedding_service: EmbeddingService, indexing_service: IndexingService, top_k: int = 10):
        self.embedding_service = embedding_service
        self.indexing_service = indexing_service
        self.top_k = top_k

    async def retrieve_context(self, question: str) -> RAGContext:
        collection = self.indexing_service.get_collection()

        # If collection is empty, return empty context (sql_generator will use full schema)
        if collection.count() == 0:
            logger.warning("ChromaDB collection is empty — returning empty RAG context")
            return RAGContext()

        # Try vector search first, fallback to keyword search
        try:
            query_embedding = await self.embedding_service.embed(question)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(self.top_k, collection.count()),
            )
        except Exception as e:
            logger.warning("Embedding API failed (%s), falling back to keyword search", e)
            results = collection.query(
                query_texts=[question],
                n_results=min(self.top_k, collection.count()),
            )

        return self._parse_results(results)

    def _parse_results(self, results: dict) -> RAGContext:
        context = RAGContext()
        seen_tables: set[str] = set()

        if not results["documents"] or not results["documents"][0]:
            return context

        for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
            doc_type = metadata.get("doc_type", "")

            if doc_type in ("table", "column"):
                table_name = metadata.get("table_name", "")
                if table_name and table_name not in seen_tables:
                    seen_tables.add(table_name)
                    context.relevant_tables.append(table_name)
                if doc_type == "table":
                    context.table_descriptions.append(doc)

            elif doc_type == "glossary":
                context.glossary_terms.append(doc)

            elif doc_type == "example":
                context.few_shot_examples.append(doc)

        logger.info(
            "RAG retrieved: %d tables, %d glossary, %d examples",
            len(context.relevant_tables),
            len(context.glossary_terms),
            len(context.few_shot_examples),
        )
        return context
