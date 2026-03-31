"use client";

import { HistoryItem } from "@/lib/types";

interface QueryHistoryProps {
  items: HistoryItem[];
  onSelect: (question: string) => void;
}

export default function QueryHistory({ items, onSelect }: QueryHistoryProps) {
  if (items.length === 0) {
    return (
      <div className="p-4 text-sm text-gray-500">No query history yet.</div>
    );
  }

  return (
    <div className="space-y-1">
      <h3 className="px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
        History
      </h3>
      {items.map((item) => (
        <button
          key={item.id}
          onClick={() => onSelect(item.question)}
          className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors group"
        >
          <p className="text-gray-700 dark:text-gray-300 truncate group-hover:text-blue-600 dark:group-hover:text-blue-400">
            {item.question}
          </p>
          <div className="flex items-center gap-2 mt-0.5">
            <span
              className={`w-1.5 h-1.5 rounded-full ${item.success ? "bg-green-500" : "bg-red-500"}`}
            />
            <span className="text-[10px] text-gray-400">
              {new Date(item.timestamp).toLocaleTimeString()}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
}
