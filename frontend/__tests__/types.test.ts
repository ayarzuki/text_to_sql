import {
  QueryResult,
  QueryResponse,
  ColumnInfo,
  TableInfo,
  SchemaResponse,
  HistoryItem,
  HistoryResponse,
} from "@/lib/types";

describe("TypeScript Interfaces", () => {
  it("QueryResult has correct shape", () => {
    const result: QueryResult = {
      columns: ["name"],
      rows: [["Budi"]],
      row_count: 1,
    };
    expect(result.columns).toHaveLength(1);
    expect(result.row_count).toBe(1);
  });

  it("QueryResponse with results", () => {
    const response: QueryResponse = {
      question: "test",
      generated_sql: "SELECT 1;",
      results: { columns: ["1"], rows: [[1]], row_count: 1 },
      execution_time_ms: 5,
      retrieved_tables: ["customers"],
    };
    expect(response.results).not.toBeNull();
    expect(response.retrieved_tables).toContain("customers");
  });

  it("QueryResponse without results", () => {
    const response: QueryResponse = {
      question: "test",
      generated_sql: "SELECT 1;",
      results: null,
      execution_time_ms: null,
      retrieved_tables: [],
    };
    expect(response.results).toBeNull();
  });

  it("SchemaResponse has tables with columns", () => {
    const schema: SchemaResponse = {
      tables: [
        {
          name: "customers",
          columns: [
            { name: "id", type: "INTEGER", nullable: false, primary_key: true },
            { name: "name", type: "TEXT", nullable: false, primary_key: false },
          ],
        },
      ],
    };
    expect(schema.tables[0].columns).toHaveLength(2);
    expect(schema.tables[0].columns[0].primary_key).toBe(true);
  });

  it("HistoryResponse has queries", () => {
    const history: HistoryResponse = {
      queries: [
        {
          id: 1,
          question: "test",
          sql: "SELECT 1",
          success: true,
          timestamp: "2026-03-29T10:00:00Z",
        },
      ],
    };
    expect(history.queries).toHaveLength(1);
    expect(history.queries[0].success).toBe(true);
  });
});
