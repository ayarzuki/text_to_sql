import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import get_settings
from middleware.security import limiter
from routers import query, schema, history, index
from services.llm_service import LLMService
from services.embedding_service import EmbeddingService
from services.schema_inspector import SchemaInspector
from services.sql_executor import SQLExecutor
from services.sql_generator import SQLGenerator
from services.rag_service import RAGService
from services.indexing_service import IndexingService
from services.history_store import HistoryStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Initialize services
    schema_inspector = SchemaInspector(settings.DATABASE_URL)
    sql_executor = SQLExecutor(settings.DATABASE_URL, max_rows=settings.MAX_RESULT_ROWS)
    llm_service = LLMService(settings.GLM_API_KEY, settings.GLM_BASE_URL, settings.GLM_MODEL)
    embedding_service = EmbeddingService(settings.GLM_API_KEY, settings.GLM_BASE_URL, settings.GLM_EMBEDDING_MODEL)
    indexing_service = IndexingService(schema_inspector, embedding_service, settings.CHROMA_PERSIST_DIR)
    rag_service = RAGService(embedding_service, indexing_service, top_k=settings.RAG_TOP_K)
    sql_generator = SQLGenerator(llm_service, rag_service, schema_inspector)
    history_store = HistoryStore()

    # Store in app state
    app.state.schema_inspector = schema_inspector
    app.state.sql_executor = sql_executor
    app.state.sql_generator = sql_generator
    app.state.indexing_service = indexing_service
    app.state.history_store = history_store

    # Auto-index on startup if collection is empty
    collection = indexing_service.get_collection()
    if collection.count() == 0:
        logger.info("ChromaDB collection is empty — running initial index...")
        try:
            count = await indexing_service.rebuild_index()
            logger.info("Initial indexing complete: %d documents", count)
        except Exception as e:
            logger.warning("Initial indexing failed (will work without RAG): %s", e)

    logger.info("Text-to-SQL backend started")
    yield
    logger.info("Text-to-SQL backend shutting down")


app = FastAPI(
    title="Text-to-SQL API",
    description="Convert natural language questions to SQL using GLM + RAG",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(query.router)
app.include_router(schema.router)
app.include_router(history.router)
app.include_router(index.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
