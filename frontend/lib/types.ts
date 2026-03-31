export interface QueryResult {
  columns: string[];
  rows: any[][];
  row_count: number;
}

export interface QueryResponse {
  question: string;
  generated_sql: string;
  results: QueryResult | null;
  execution_time_ms: number | null;
  retrieved_tables: string[];
}

export interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
}

export interface TableInfo {
  name: string;
  columns: ColumnInfo[];
}

export interface SchemaResponse {
  tables: TableInfo[];
}

export interface HistoryItem {
  id: number;
  question: string;
  sql: string;
  success: boolean;
  timestamp: string;
}

export interface HistoryResponse {
  queries: HistoryItem[];
}
