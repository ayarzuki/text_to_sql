import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def app_client(test_db, chroma_dir):
    """Create a test client with lifespan properly initialized."""
    os.environ["DATABASE_URL"] = f"sqlite:///{test_db}"
    os.environ["CHROMA_PERSIST_DIR"] = chroma_dir

    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Trigger lifespan startup
        from services.schema_inspector import SchemaInspector
        from services.sql_executor import SQLExecutor
        from services.sql_generator import SQLGenerator
        from services.llm_service import LLMService
        from services.embedding_service import EmbeddingService
        from services.rag_service import RAGService
        from services.indexing_service import IndexingService
        from services.history_store import HistoryStore
        from config import get_settings

        get_settings.cache_clear()
        s = get_settings()

        schema_inspector = SchemaInspector(f"sqlite:///{test_db}")
        sql_executor = SQLExecutor(f"sqlite:///{test_db}", max_rows=s.MAX_RESULT_ROWS)
        llm_service = LLMService(s.GLM_API_KEY, s.GLM_BASE_URL, s.GLM_MODEL)
        embedding_service = EmbeddingService(s.GLM_API_KEY, s.GLM_BASE_URL, s.GLM_EMBEDDING_MODEL)
        indexing_service = IndexingService(schema_inspector, embedding_service, chroma_dir)
        rag_service = RAGService(embedding_service, indexing_service, top_k=s.RAG_TOP_K)
        sql_generator = SQLGenerator(llm_service, rag_service, schema_inspector)
        history_store = HistoryStore()

        app.state.schema_inspector = schema_inspector
        app.state.sql_executor = sql_executor
        app.state.sql_generator = sql_generator
        app.state.indexing_service = indexing_service
        app.state.history_store = history_store

        yield ac


class TestHealthEndpoint:
    async def test_health(self, app_client):
        response = await app_client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSchemaEndpoint:
    async def test_get_schema(self, app_client):
        response = await app_client.get("/api/schema")
        assert response.status_code == 200

        data = response.json()
        assert "tables" in data
        table_names = [t["name"] for t in data["tables"]]
        assert "customers" in table_names
        assert "products" in table_names
        assert "orders" in table_names

    async def test_schema_has_columns(self, app_client):
        response = await app_client.get("/api/schema")
        data = response.json()

        customers = next(t for t in data["tables"] if t["name"] == "customers")
        col_names = [c["name"] for c in customers["columns"]]
        assert "id" in col_names
        assert "name" in col_names


class TestHistoryEndpoint:
    async def test_empty_history(self, app_client):
        response = await app_client.get("/api/history")
        assert response.status_code == 200
        assert response.json() == {"queries": []}

    async def test_history_with_limit(self, app_client):
        response = await app_client.get("/api/history?limit=10")
        assert response.status_code == 200


class TestQueryEndpoint:
    async def test_query_empty_question_rejected(self, app_client):
        response = await app_client.post("/api/query", json={"question": "", "execute": False})
        assert response.status_code == 422

    async def test_query_too_long_rejected(self, app_client):
        response = await app_client.post("/api/query", json={"question": "x" * 1001, "execute": False})
        assert response.status_code == 422


class TestIndexEndpoint:
    async def test_rebuild_index(self, app_client):
        response = await app_client.post("/api/index/rebuild")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert data["documents_indexed"] > 0
