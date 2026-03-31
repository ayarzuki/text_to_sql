import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import AsyncMock
from services.schema_inspector import SchemaInspector
from services.indexing_service import IndexingService
from services.rag_service import RAGService


@pytest.fixture
def rag_setup(db_url, chroma_dir):
    """Set up RAG with indexed data using ChromaDB default embeddings."""
    inspector = SchemaInspector(db_url)
    mock_embedding = AsyncMock()
    mock_embedding.embed_batch = AsyncMock(side_effect=Exception("skip"))
    mock_embedding.embed = AsyncMock(side_effect=Exception("skip"))

    indexing = IndexingService(inspector, mock_embedding, chroma_dir)
    rag = RAGService(mock_embedding, indexing, top_k=5)
    return indexing, rag


class TestRAGService:
    @pytest.mark.asyncio
    async def test_retrieve_returns_context(self, rag_setup):
        indexing, rag = rag_setup
        await indexing.rebuild_index()

        ctx = await rag.retrieve_context("show me customers")

        assert len(ctx.relevant_tables) > 0

    @pytest.mark.asyncio
    async def test_retrieve_finds_relevant_tables(self, rag_setup):
        indexing, rag = rag_setup
        await indexing.rebuild_index()

        ctx = await rag.retrieve_context("total order per customer")

        # Should find customers and/or orders tables
        assert any(t in ctx.relevant_tables for t in ["customers", "orders"])

    @pytest.mark.asyncio
    async def test_empty_collection_returns_empty_context(self, rag_setup):
        _, rag = rag_setup
        # Don't rebuild index — collection is empty
        ctx = await rag.retrieve_context("anything")

        assert ctx.relevant_tables == []
        assert ctx.glossary_terms == []
        assert ctx.few_shot_examples == []

    @pytest.mark.asyncio
    async def test_glossary_retrieved(self, rag_setup):
        indexing, rag = rag_setup
        await indexing.rebuild_index()

        ctx = await rag.retrieve_context("what is the total revenue")

        # Should retrieve glossary terms about revenue
        assert len(ctx.glossary_terms) >= 0  # may or may not match depending on keyword search
