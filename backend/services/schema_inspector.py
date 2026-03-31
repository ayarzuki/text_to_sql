from sqlalchemy import create_engine, inspect
from models.response import TableInfo, ColumnInfo


class SchemaInspector:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self._is_sqlite = database_url.startswith("sqlite")

    def _schema(self) -> str | None:
        return None if self._is_sqlite else "public"

    def get_all_tables(self) -> list[TableInfo]:
        inspector = inspect(self.engine)
        schema = self._schema()
        tables = []

        for table_name in inspector.get_table_names(schema=schema):
            columns = []
            pk_columns = {col for col in inspector.get_pk_constraint(table_name, schema=schema).get("constrained_columns", [])}

            for col in inspector.get_columns(table_name, schema=schema):
                columns.append(ColumnInfo(
                    name=col["name"],
                    type=str(col["type"]),
                    nullable=col.get("nullable", True),
                    primary_key=col["name"] in pk_columns,
                ))

            tables.append(TableInfo(name=table_name, columns=columns))

        return tables

    def get_tables_as_ddl(self, table_names: list[str] | None = None) -> str:
        all_tables = self.get_all_tables()

        if table_names:
            all_tables = [t for t in all_tables if t.name in table_names]

        ddl_parts = []
        for table in all_tables:
            cols = []
            for c in table.columns:
                pk = " PRIMARY KEY" if c.primary_key else ""
                null = "" if c.nullable else " NOT NULL"
                cols.append(f"  {c.name} {c.type}{pk}{null}")
            ddl_parts.append(f"CREATE TABLE {table.name} (\n" + ",\n".join(cols) + "\n);")

        # Add foreign key info
        inspector = inspect(self.engine)
        schema = self._schema()
        for table in all_tables:
            for fk in inspector.get_foreign_keys(table.name, schema=schema):
                referred = fk["referred_table"]
                local_cols = ", ".join(fk["constrained_columns"])
                remote_cols = ", ".join(fk["referred_columns"])
                ddl_parts.append(f"-- FK: {table.name}({local_cols}) -> {referred}({remote_cols})")

        return "\n\n".join(ddl_parts)
