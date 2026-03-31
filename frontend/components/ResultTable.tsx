"use client";

import { QueryResult } from "@/lib/types";

interface ResultTableProps {
  result: QueryResult;
  executionTimeMs: number | null;
}

export default function ResultTable({ result, executionTimeMs }: ResultTableProps) {
  if (result.row_count === 0) {
    return (
      <div className="rounded-xl border border-gray-200 dark:border-gray-800 p-8 text-center text-gray-500">
        Query executed successfully but returned no rows.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
          Results
        </span>
        <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
          <span>{result.row_count} rows</span>
          {executionTimeMs !== null && <span>{executionTimeMs}ms</span>}
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
              {result.columns.map((col) => (
                <th
                  key={col}
                  className="px-4 py-2.5 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wide"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.rows.map((row, i) => (
              <tr
                key={i}
                className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors"
              >
                {row.map((cell, j) => (
                  <td
                    key={j}
                    className="px-4 py-2.5 text-gray-700 dark:text-gray-300 font-mono text-xs"
                  >
                    {cell === null ? (
                      <span className="text-gray-400 italic">NULL</span>
                    ) : (
                      String(cell)
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
