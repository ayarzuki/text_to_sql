from fastapi import APIRouter, Request
from models.response import SchemaResponse

router = APIRouter(prefix="/api", tags=["schema"])


@router.get("/schema", response_model=SchemaResponse)
async def get_schema(request: Request):
    schema_inspector = request.app.state.schema_inspector
    tables = schema_inspector.get_all_tables()
    return SchemaResponse(tables=tables)
