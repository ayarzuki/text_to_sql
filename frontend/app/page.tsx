"use client";

import { useState, useCallback } from "react";
import ChatInput from "@/components/ChatInput";
import SQLPreview from "@/components/SQLPreview";
import ResultTable from "@/components/ResultTable";
import SchemaViewer from "@/components/SchemaViewer";
import QueryHistory from "@/components/QueryHistory";
import ErrorBanner from "@/components/ErrorBanner";
import { submitQuery, getHistory } from "@/lib/api";
import { QueryResponse, HistoryItem } from "@/lib/types";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [sidebarTab, setSidebarTab] = useState<"schema" | "history">("schema");

  const refreshHistory = useCallback(async () => {
    try {
      const res = await getHistory();
      setHistory(res.queries);
    } catch {}
  }, []);

  const handleSubmit = async (question: string) => {
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await submitQuery(question, true);
      setResponse(res);
      await refreshHistory();
    } catch (e: any) {
      setError(e.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const handleHistorySelect = (question: string) => {
    handleSubmit(question);
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-72 border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 flex flex-col shrink-0">
        {/* Logo */}
        <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-800">
          <h1 className="text-lg font-bold text-gray-900 dark:text-white">
            Text to SQL
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            AI-powered query generator
          </p>
        </div>

        {/* Sidebar tabs */}
        <div className="flex border-b border-gray-200 dark:border-gray-800">
          <button
            onClick={() => setSidebarTab("schema")}
            className={`flex-1 py-2.5 text-xs font-medium transition-colors ${
              sidebarTab === "schema"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Schema
          </button>
          <button
            onClick={() => {
              setSidebarTab("history");
              refreshHistory();
            }}
            className={`flex-1 py-2.5 text-xs font-medium transition-colors ${
              sidebarTab === "history"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            History
          </button>
        </div>

        {/* Sidebar content */}
        <div className="flex-1 overflow-y-auto p-2">
          {sidebarTab === "schema" ? (
            <SchemaViewer />
          ) : (
            <QueryHistory items={history} onSelect={handleHistorySelect} />
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Results area */}
        <div className="flex-1 overflow-y-auto p-6">
          {!response && !error && !loading && (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-2xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Ask your database
              </h2>
              <p className="text-sm text-gray-500 max-w-md">
                Type a question in natural language and AI will generate the SQL
                query for you. For example: &quot;Show top 5 customers by total
                orders&quot;
              </p>
            </div>
          )}

          <div className="max-w-4xl mx-auto space-y-4">
            {error && (
              <ErrorBanner
                message={error}
                onDismiss={() => setError(null)}
              />
            )}

            {response && (
              <>
                {/* Question */}
                <div className="px-4 py-3 rounded-xl bg-blue-50 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900">
                  <p className="text-sm text-blue-800 dark:text-blue-300">
                    {response.question}
                  </p>
                </div>

                {/* SQL Preview */}
                <SQLPreview
                  sql={response.generated_sql}
                  retrievedTables={response.retrieved_tables}
                />

                {/* Result Table */}
                {response.results && (
                  <ResultTable
                    result={response.results}
                    executionTimeMs={response.execution_time_ms}
                  />
                )}
              </>
            )}

            {loading && (
              <div className="flex items-center justify-center py-12">
                <div className="flex items-center gap-3 text-gray-500">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <span className="text-sm">Generating SQL...</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Input area */}
        <div className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 p-4">
          <div className="max-w-4xl mx-auto">
            <ChatInput onSubmit={handleSubmit} loading={loading} />
          </div>
        </div>
      </main>
    </div>
  );
}
