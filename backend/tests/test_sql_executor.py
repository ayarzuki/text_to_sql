import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from services.sql_executor import SQLExecutor


class TestSQLExecutor:
    def test_execute_simple_select(self, db_url):
        executor = SQLExecutor(db_url)
        result, elapsed = executor.execute("SELECT * FROM customers")

        assert result.row_count == 2
        assert "name" in result.columns
        assert elapsed >= 0

    def test_execute_with_where(self, db_url):
        executor = SQLExecutor(db_url)
        result, _ = executor.execute("SELECT name FROM customers WHERE city = 'Jakarta'")

        assert result.row_count == 1
        assert result.rows[0][0] == "Budi"

    def test_execute_aggregation(self, db_url):
        executor = SQLExecutor(db_url)
        result, _ = executor.execute("SELECT COUNT(*) as cnt FROM orders")

        assert result.columns == ["cnt"]
        assert result.rows[0][0] == 3

    def test_execute_join(self, db_url):
        executor = SQLExecutor(db_url)
        result, _ = executor.execute(
            "SELECT c.name, o.total_price FROM customers c "
            "JOIN orders o ON c.id = o.customer_id ORDER BY o.total_price DESC"
        )

        assert result.row_count == 3
        assert result.columns == ["name", "total_price"]

    def test_max_rows_limit(self, db_url):
        executor = SQLExecutor(db_url, max_rows=1)
        result, _ = executor.execute("SELECT * FROM orders")

        assert result.row_count == 1

    def test_invalid_sql_raises(self, db_url):
        executor = SQLExecutor(db_url)
        with pytest.raises(Exception):
            executor.execute("SELECT * FROM nonexistent_table")
