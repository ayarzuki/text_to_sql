import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pydantic import ValidationError
from models.request import QueryRequest
from models.response import QueryResult, QueryResponse, HistoryItem
from datetime import datetime, timezone


class TestQueryRequest:
    def test_valid_request(self):
        req = QueryRequest(question="Show all customers")
        assert req.question == "Show all customers"
        assert req.execute is True

    def test_execute_false(self):
        req = QueryRequest(question="test", execute=False)
        assert req.execute is False

    def test_empty_question_rejected(self):
        with pytest.raises(ValidationError):
            QueryRequest(question="")

    def test_too_long_question_rejected(self):
        with pytest.raises(ValidationError):
            QueryRequest(question="x" * 1001)


class TestQueryResult:
    def test_valid_result(self):
        result = QueryResult(
            columns=["name", "city"],
            rows=[["Budi", "Jakarta"]],
            row_count=1,
        )
        assert result.row_count == 1

    def test_empty_result(self):
        result = QueryResult(columns=[], rows=[], row_count=0)
        assert result.row_count == 0


class TestQueryResponse:
    def test_full_response(self):
        resp = QueryResponse(
            question="test",
            generated_sql="SELECT 1;",
            results=QueryResult(columns=["1"], rows=[[1]], row_count=1),
            execution_time_ms=5,
            retrieved_tables=["customers"],
        )
        assert resp.generated_sql == "SELECT 1;"

    def test_response_without_results(self):
        resp = QueryResponse(
            question="test",
            generated_sql="SELECT 1;",
        )
        assert resp.results is None
        assert resp.execution_time_ms is None


class TestHistoryItem:
    def test_history_item(self):
        item = HistoryItem(
            id=1,
            question="test",
            sql="SELECT 1",
            success=True,
            timestamp=datetime.now(timezone.utc),
        )
        assert item.id == 1
        assert item.success is True
