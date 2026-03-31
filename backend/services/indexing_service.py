import json
import logging
from pathlib import Path

import chromadb

from services.embedding_service import EmbeddingService
from services.schema_inspector import SchemaInspector

logger = logging.getLogger(__name__)

COLLECTION_NAME = "text_to_sql"


class IndexingService:
    def __init__(
        self,
        schema_inspector: SchemaInspector,
        embedding_service: EmbeddingService,
        chroma_persist_dir: str,
    ):
        self.schema_inspector = schema_inspector
        self.embedding_service = embedding_service
        self.chroma_client = chromadb.PersistentClient(path=chroma_persist_dir)

    def get_collection(self) -> chromadb.Collection:
        return self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    async def rebuild_index(self) -> int:
        # Delete existing collection and recreate
        try:
            self.chroma_client.delete_collection(COLLECTION_NAME)
        except ValueError:
            pass

        collection = self.get_collection()

        documents: list[dict] = []

        # 1. Index table schemas
        tables = self.schema_inspector.get_all_tables()
        for table in tables:
            cols_desc = ", ".join(
                f"{c.name} ({c.type}{'  PK' if c.primary_key else ''})"
                for c in table.columns
            )
            doc_text = f"Table: {table.name}. Columns: {cols_desc}"
            documents.append({
                "id": f"table_{table.name}",
                "text": doc_text,
                "metadata": {"doc_type": "table", "table_name": table.name},
            })

            # Index each column individually for fine-grained retrieval
            for col in table.columns:
                col_text = f"Column {col.name} in table {table.name}, type {col.type}"
                if col.primary_key:
                    col_text += ", primary key"
                documents.append({
                    "id": f"col_{table.name}_{col.name}",
                    "text": col_text,
                    "metadata": {"doc_type": "column", "table_name": table.name, "column_name": col.name},
                })

        # 2. Index knowledge base files (glossary + examples)
        kb_path = Path(__file__).parent.parent / "knowledge_base"
        for jsonl_file in kb_path.rglob("*.jsonl"):
            for line in jsonl_file.read_text(encoding="utf-8").strip().splitlines():
                if not line.strip():
                    continue
                entry = json.loads(line)
                doc_type = entry.get("doc_type", "unknown")
                doc_id = f"{doc_type}_{entry.get('term', entry.get('question', ''))[:50]}"

                if doc_type == "glossary":
                    text = f"Business term: {entry['term']}. Definition: {entry['definition']}"
                elif doc_type == "example":
                    text = f"Example question: {entry['question']}. SQL: {entry['sql']}"
                else:
                    text = json.dumps(entry)

                documents.append({
                    "id": doc_id,
                    "text": text,
                    "metadata": {"doc_type": doc_type, **{k: v for k, v in entry.items() if isinstance(v, (str, int, float, bool))}},
                })

        if not documents:
            return 0

        # Embed in batches — fallback to ChromaDB default embedding if API fails
        batch_size = 20
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            texts = [d["text"] for d in batch]

            try:
                embeddings = await self.embedding_service.embed_batch(texts)
                collection.add(
                    ids=[d["id"] for d in batch],
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=[d["metadata"] for d in batch],
                )
            except Exception as e:
                logger.warning("Embedding API failed (%s), using ChromaDB default embeddings", e)
                collection.add(
                    ids=[d["id"] for d in batch],
                    documents=texts,
                    metadatas=[d["metadata"] for d in batch],
                )

        logger.info("Indexed %d documents into ChromaDB", len(documents))
        return len(documents)
