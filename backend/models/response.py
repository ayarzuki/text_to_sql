from pydantic import BaseModel
from typing import Any
from datetime import datetime


class QueryResult(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int


class QueryResponse(BaseModel):
    question: str
    generated_sql: str
    results: QueryResult | None = None
    execution_time_ms: int | None = None
    retrieved_tables: list[str] = []


class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool = False


class TableInfo(BaseModel):
    name: str
    columns: list[ColumnInfo]


class SchemaResponse(BaseModel):
    tables: list[TableInfo]


class HistoryItem(BaseModel):
    id: int
    question: str
    sql: str
    success: bool
    timestamp: datetime


class HistoryResponse(BaseModel):
    queries: list[HistoryItem]
