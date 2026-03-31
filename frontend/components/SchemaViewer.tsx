"use client";

import { useState, useEffect } from "react";
import { getSchema } from "@/lib/api";
import { TableInfo } from "@/lib/types";

export default function SchemaViewer() {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSchema()
      .then((res) => setTables(res.tables))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const toggle = (name: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="p-4 text-sm text-gray-500 animate-pulse">
        Loading schema...
      </div>
    );
  }

  if (tables.length === 0) {
    return (
      <div className="p-4 text-sm text-gray-500">No tables found.</div>
    );
  }

  return (
    <div className="space-y-1">
      <h3 className="px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
        Database Schema
      </h3>
      {tables.map((table) => (
        <div key={table.name}>
          <button
            onClick={() => toggle(table.name)}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <svg
              className={`w-3 h-3 text-gray-400 transition-transform ${expanded.has(table.name) ? "rotate-90" : ""}`}
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path d="M6 4l8 6-8 6V4z" />
            </svg>
            <span className="font-mono text-blue-600 dark:text-blue-400">
              {table.name}
            </span>
            <span className="text-xs text-gray-400 ml-auto">
              {table.columns.length} cols
            </span>
          </button>
          {expanded.has(table.name) && (
            <div className="ml-8 mb-2 space-y-0.5">
              {table.columns.map((col) => (
                <div
                  key={col.name}
                  className="flex items-center gap-2 px-2 py-1 text-xs"
                >
                  <span className="font-mono text-gray-700 dark:text-gray-300">
                    {col.name}
                  </span>
                  <span className="text-gray-400">{col.type}</span>
                  {col.primary_key && (
                    <span className="px-1.5 py-0.5 text-[10px] rounded bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400">
                      PK
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
