import { QueryResponse, SchemaResponse, HistoryResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error: ${res.status}`);
  }

  return res.json();
}

export async function submitQuery(
  question: string,
  execute: boolean = true
): Promise<QueryResponse> {
  return fetchAPI<QueryResponse>("/api/query", {
    method: "POST",
    body: JSON.stringify({ question, execute }),
  });
}

export async function getSchema(): Promise<SchemaResponse> {
  return fetchAPI<SchemaResponse>("/api/schema");
}

export async function getHistory(limit = 50): Promise<HistoryResponse> {
  return fetchAPI<HistoryResponse>(`/api/history?limit=${limit}`);
}

export async function rebuildIndex(): Promise<{ status: string; documents_indexed: number }> {
  return fetchAPI("/api/index/rebuild", { method: "POST" });
}
