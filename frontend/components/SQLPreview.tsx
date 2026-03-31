"use client";

interface SQLPreviewProps {
  sql: string;
  retrievedTables: string[];
}

export default function SQLPreview({ sql, retrievedTables }: SQLPreviewProps) {
  const copyToClipboard = () => {
    navigator.clipboard.writeText(sql);
  };

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-900 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
            Generated SQL
          </span>
          {retrievedTables.length > 0 && (
            <div className="flex gap-1">
              {retrievedTables.map((t) => (
                <span
                  key={t}
                  className="px-2 py-0.5 text-[10px] rounded-full bg-blue-500/20 text-blue-400 font-mono"
                >
                  {t}
                </span>
              ))}
            </div>
          )}
        </div>
        <button
          onClick={copyToClipboard}
          className="text-xs text-gray-400 hover:text-white transition-colors px-2 py-1 rounded hover:bg-gray-700"
        >
          Copy
        </button>
      </div>
      <pre className="p-4 text-sm text-green-400 font-mono overflow-x-auto whitespace-pre-wrap">
        {sql}
      </pre>
    </div>
  );
}
