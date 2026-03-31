import { submitQuery, getSchema, getHistory, rebuildIndex } from "@/lib/api";

// Mock global fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

beforeEach(() => {
  mockFetch.mockClear();
});

describe("submitQuery", () => {
  it("sends POST request with question", async () => {
    const mockResponse = {
      question: "test",
      generated_sql: "SELECT 1;",
      results: { columns: ["1"], rows: [[1]], row_count: 1 },
      execution_time_ms: 5,
      retrieved_tables: [],
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await submitQuery("test question");

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/query"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ question: "test question", execute: true }),
      })
    );
    expect(result.generated_sql).toBe("SELECT 1;");
  });

  it("sends execute=false when specified", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ question: "test", generated_sql: "SELECT 1;" }),
    });

    await submitQuery("test", false);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({
        body: JSON.stringify({ question: "test", execute: false }),
      })
    );
  });

  it("throws on API error", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 502,
      json: async () => ({ detail: "LLM API error" }),
    });

    await expect(submitQuery("test")).rejects.toThrow("LLM API error");
  });
});

describe("getSchema", () => {
  it("sends GET request to /api/schema", async () => {
    const mockSchema = {
      tables: [
        { name: "customers", columns: [{ name: "id", type: "INTEGER", nullable: false, primary_key: true }] },
      ],
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSchema,
    });

    const result = await getSchema();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/schema"),
      expect.anything()
    );
    expect(result.tables).toHaveLength(1);
    expect(result.tables[0].name).toBe("customers");
  });
});

describe("getHistory", () => {
  it("sends GET request with limit param", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ queries: [] }),
    });

    await getHistory(20);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/history?limit=20"),
      expect.anything()
    );
  });
});

describe("rebuildIndex", () => {
  it("sends POST to /api/index/rebuild", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: "ok", documents_indexed: 30 }),
    });

    const result = await rebuildIndex();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/index/rebuild"),
      expect.objectContaining({ method: "POST" })
    );
    expect(result.documents_indexed).toBe(30);
  });
});
