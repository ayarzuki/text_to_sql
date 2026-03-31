from fastapi import APIRouter, Request, HTTPException, Depends
from models.request import QueryRequest
from models.response import QueryResponse
from middleware.security import limiter

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResponse)
@limiter.limit("20/minute")
async def generate_and_execute_query(request: Request, body: QueryRequest):
    sql_generator = request.app.state.sql_generator
    sql_executor = request.app.state.sql_executor
    history_store = request.app.state.history_store

    try:
        sql, retrieved_tables = await sql_generator.generate(body.question)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid SQL generated: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM API error: {e}")

    results = None
    execution_time_ms = None
    success = True

    if body.execute:
        try:
            results, execution_time_ms = sql_executor.execute(sql)
        except Exception as e:
            success = False
            raise HTTPException(status_code=400, detail=f"SQL execution error: {e}")
        finally:
            history_store.add(body.question, sql, success)
    else:
        history_store.add(body.question, sql, success)

    return QueryResponse(
        question=body.question,
        generated_sql=sql,
        results=results,
        execution_time_ms=execution_time_ms,
        retrieved_tables=retrieved_tables,
    )
