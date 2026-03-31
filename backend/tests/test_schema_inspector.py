import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.schema_inspector import SchemaInspector


class TestSchemaInspector:
    def test_get_all_tables(self, db_url):
        inspector = SchemaInspector(db_url)
        tables = inspector.get_all_tables()
        table_names = [t.name for t in tables]

        assert "customers" in table_names
        assert "products" in table_names
        assert "orders" in table_names

    def test_table_columns(self, db_url):
        inspector = SchemaInspector(db_url)
        tables = inspector.get_all_tables()
        customers = next(t for t in tables if t.name == "customers")
        col_names = [c.name for c in customers.columns]

        assert "id" in col_names
        assert "name" in col_names
        assert "email" in col_names
        assert "city" in col_names

    def test_primary_key_detection(self, db_url):
        inspector = SchemaInspector(db_url)
        tables = inspector.get_all_tables()
        customers = next(t for t in tables if t.name == "customers")
        id_col = next(c for c in customers.columns if c.name == "id")

        assert id_col.primary_key is True

    def test_get_tables_as_ddl(self, db_url):
        inspector = SchemaInspector(db_url)
        ddl = inspector.get_tables_as_ddl()

        assert "CREATE TABLE customers" in ddl
        assert "CREATE TABLE products" in ddl
        assert "CREATE TABLE orders" in ddl

    def test_get_tables_as_ddl_filtered(self, db_url):
        inspector = SchemaInspector(db_url)
        ddl = inspector.get_tables_as_ddl(["customers"])

        assert "CREATE TABLE customers" in ddl
        assert "CREATE TABLE products" not in ddl

    def test_foreign_keys_in_ddl(self, db_url):
        inspector = SchemaInspector(db_url)
        ddl = inspector.get_tables_as_ddl()

        assert "FK:" in ddl
        assert "customers" in ddl
