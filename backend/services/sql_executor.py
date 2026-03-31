import time
import logging
from sqlalchemy import create_engine, text
from models.response import QueryResult

logger = logging.getLogger(__name__)


class SQLExecutor:
    def __init__(self, database_url: str, max_rows: int = 1000):
        self.engine = create_engine(database_url)
        self.max_rows = max_rows

    def execute(self, sql: str) -> tuple[QueryResult, int]:
        start = time.perf_counter()

        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = [list(row) for row in result.fetchmany(self.max_rows)]

        elapsed_ms = int((time.perf_counter() - start) * 1000)

        logger.info("Executed SQL in %dms, returned %d rows", elapsed_ms, len(rows))

        return QueryResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
        ), elapsed_ms
