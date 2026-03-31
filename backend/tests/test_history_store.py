import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.history_store import HistoryStore


class TestHistoryStore:
    def test_add_and_get(self):
        store = HistoryStore()
        store.add("question 1", "SELECT 1", True)
        store.add("question 2", "SELECT 2", False)

        items = store.get_all()
        assert len(items) == 2
        # Most recent first
        assert items[0].question == "question 2"
        assert items[1].question == "question 1"

    def test_success_flag(self):
        store = HistoryStore()
        store.add("q", "SELECT 1", True)
        store.add("q", "BAD SQL", False)

        items = store.get_all()
        assert items[0].success is False
        assert items[1].success is True

    def test_limit(self):
        store = HistoryStore()
        for i in range(10):
            store.add(f"q{i}", f"SELECT {i}", True)

        items = store.get_all(limit=3)
        assert len(items) == 3
        # Should return the 3 most recent
        assert items[0].question == "q9"

    def test_auto_increment_id(self):
        store = HistoryStore()
        store.add("a", "SELECT 1", True)
        store.add("b", "SELECT 2", True)

        items = store.get_all()
        assert items[0].id == 2
        assert items[1].id == 1

    def test_empty_store(self):
        store = HistoryStore()
        assert store.get_all() == []
