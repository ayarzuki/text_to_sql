import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from services.sql_generator import SQLGenerator


class TestSQLValidation:
    @pytest.fixture
    def generator(self):
        gen = SQLGenerator.__new__(SQLGenerator)
        return gen

    @pytest.mark.parametrize("sql", [
        "SELECT * FROM customers;",
        "SELECT c.name, COUNT(o.id) FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name;",
        "SELECT name FROM customers WHERE city = 'Jakarta';",
        "SELECT AVG(total_price) FROM orders WHERE status = 'completed';",
    ])
    def test_valid_select_passes(self, generator, sql):
        generator._validate_sql(sql)

    @pytest.mark.parametrize("sql,keyword", [
        ("DROP TABLE customers;", "DROP"),
        ("DELETE FROM orders;", "DELETE"),
        ("INSERT INTO customers VALUES (1, 'test');", "INSERT"),
        ("UPDATE orders SET status = 'cancelled';", "UPDATE"),
        ("ALTER TABLE customers ADD COLUMN age INT;", "ALTER"),
        ("TRUNCATE TABLE orders;", "TRUNCATE"),
        ("CREATE TABLE hacked (id INT);", "CREATE"),
        ("GRANT ALL ON customers TO public;", "GRANT"),
        ("REVOKE SELECT ON customers FROM public;", "REVOKE"),
    ])
    def test_forbidden_keywords_rejected(self, generator, sql, keyword):
        with pytest.raises(ValueError, match=keyword):
            generator._validate_sql(sql)


class TestSQLExtraction:
    @pytest.fixture
    def generator(self):
        gen = SQLGenerator.__new__(SQLGenerator)
        return gen

    def test_extract_from_code_block(self, generator):
        raw = "```sql\nSELECT * FROM customers\n```"
        result = generator._extract_sql(raw)
        assert result == "SELECT * FROM customers"

    def test_extract_from_plain_text(self, generator):
        raw = "SELECT * FROM customers"
        result = generator._extract_sql(raw)
        assert result == "SELECT * FROM customers;"

    def test_extract_from_code_block_no_lang(self, generator):
        raw = "```\nSELECT 1\n```"
        result = generator._extract_sql(raw)
        assert result == "SELECT 1"

    def test_extract_preserves_complex_sql(self, generator):
        raw = "```sql\nSELECT c.name, SUM(o.total_price)\nFROM customers c\nJOIN orders o ON c.id = o.customer_id\nGROUP BY c.name\n```"
        result = generator._extract_sql(raw)
        assert "JOIN" in result
        assert "GROUP BY" in result
