from fastapi import APIRouter, Request, Query
from models.response import HistoryResponse

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history", response_model=HistoryResponse)
async def get_history(request: Request, limit: int = Query(default=50, le=200)):
    history_store = request.app.state.history_store
    queries = history_store.get_all(limit=limit)
    return HistoryResponse(queries=queries)
