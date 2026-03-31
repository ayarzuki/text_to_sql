import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import AsyncMock
from services.schema_inspector import SchemaInspector
from services.indexing_service import IndexingService


class TestIndexingService:
    @pytest.mark.asyncio
    async def test_rebuild_index(self, db_url, chroma_dir):
        inspector = SchemaInspector(db_url)
        mock_embedding = AsyncMock()
        # Simulate embedding API failure → triggers ChromaDB default embedding fallback
        mock_embedding.embed_batch = AsyncMock(side_effect=Exception("API unavailable"))

        service = IndexingService(inspector, mock_embedding, chroma_dir)
        count = await service.rebuild_index()

        # Should index tables + columns + knowledge base files
        assert count > 0

    @pytest.mark.asyncio
    async def test_collection_created(self, db_url, chroma_dir):
        inspector = SchemaInspector(db_url)
        mock_embedding = AsyncMock()
        mock_embedding.embed_batch = AsyncMock(side_effect=Exception("API unavailable"))

        service = IndexingService(inspector, mock_embedding, chroma_dir)
        await service.rebuild_index()

        collection = service.get_collection()
        assert collection.count() > 0

    @pytest.mark.asyncio
    async def test_tables_indexed(self, db_url, chroma_dir):
        inspector = SchemaInspector(db_url)
        mock_embedding = AsyncMock()
        mock_embedding.embed_batch = AsyncMock(side_effect=Exception("API unavailable"))

        service = IndexingService(inspector, mock_embedding, chroma_dir)
        await service.rebuild_index()

        collection = service.get_collection()
        # Query for table documents
        results = collection.get(where={"doc_type": "table"})
        table_names = [m["table_name"] for m in results["metadatas"]]

        assert "customers" in table_names
        assert "orders" in table_names
        assert "products" in table_names

    @pytest.mark.asyncio
    async def test_rebuild_clears_old_data(self, db_url, chroma_dir):
        inspector = SchemaInspector(db_url)
        mock_embedding = AsyncMock()
        mock_embedding.embed_batch = AsyncMock(side_effect=Exception("API unavailable"))

        service = IndexingService(inspector, mock_embedding, chroma_dir)

        count1 = await service.rebuild_index()
        count2 = await service.rebuild_index()

        # Should be same count after rebuild (not doubled)
        assert count1 == count2
