from datetime import datetime, timezone
from models.response import HistoryItem


class HistoryStore:
    """In-memory query history. Replace with DB-backed store for persistence."""

    def __init__(self):
        self._history: list[HistoryItem] = []
        self._counter = 0

    def add(self, question: str, sql: str, success: bool) -> None:
        self._counter += 1
        self._history.append(HistoryItem(
            id=self._counter,
            question=question,
            sql=sql,
            success=success,
            timestamp=datetime.now(timezone.utc),
        ))

    def get_all(self, limit: int = 50) -> list[HistoryItem]:
        return list(reversed(self._history[-limit:]))
