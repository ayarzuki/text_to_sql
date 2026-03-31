from fastapi import APIRouter, Request, HTTPException

router = APIRouter(prefix="/api", tags=["index"])


@router.post("/index/rebuild")
async def rebuild_index(request: Request):
    indexing_service = request.app.state.indexing_service
    try:
        count = await indexing_service.rebuild_index()
        return {"status": "ok", "documents_indexed": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")
