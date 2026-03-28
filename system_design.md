# System Design: Text-to-SQL Web Application

## 1. Overview

Aplikasi web yang memungkinkan user menginput pertanyaan dalam bahasa natural (Bahasa Indonesia/English), lalu sistem mengkonversi pertanyaan tersebut menjadi SQL query menggunakan GLM API, mengeksekusi query ke database, dan menampilkan hasilnya di UI.

## 2. Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Web UI)                 │
│              Next.js + Tailwind CSS                 │
│                                                     │
│  ┌───────────┐  ┌────────────┐  ┌───────────────┐   │
│  │ Chat Input│  │ SQL Preview│  │ Result Table  │   │
│  └─────┬─────┘  └─────▲──────┘  └──────▲────────┘   │
│        │               │               │            │
└────────┼───────────────┼───────────────┼────────────┘
         │               │               │
         ▼               │               │
┌─────────────────────────────────────────────────────┐
│                 Backend (API Server)                │
│                  FastAPI (Python)                   │
│                                                     │
│  ┌──────────┐  ┌─────────────┐  ┌───────────────┐   │
│  │ /api/    │  │  SQL        │  │  Query        │   │
│  │ query    │──▶  Generator  │──▶  Executor    │   │
│  └──────────┘  └──────┬──────┘  └──────┬────────┘   │
│                       │                │            │
└───────────────────────┼────────────────┼────────────┘
                        │                │
                        ▼                ▼
                 ┌──────────┐    ┌──────────────┐
                 │ GLM API  │    │   Database   │
                 │ (LLM)    │    │  (PostgreSQL)│
                 └──────────┘    └──────────────┘
```

## 3. Tech Stack

| Layer        | Technology              | Alasan                                           |
| ------------ | ----------------------- | ------------------------------------------------ |
| **Frontend** | Next.js 14 (App Router) | SSR, routing built-in, React ecosystem           |
| **Styling**  | Tailwind CSS            | Rapid UI development, utility-first              |
| **Backend**  | FastAPI (Python)        | Async, auto-docs (Swagger), cocok untuk AI tasks |
| **LLM**      | GLM API                 | Model bahasa untuk konversi natural language → SQL |
| **Database** | PostgreSQL              | Robust, SQL-standard, scalable                   |
| **ORM**      | SQLAlchemy              | Schema introspection untuk prompt engineering    |

## 4. Komponen Sistem

### 4.1 Frontend (Next.js)

```
frontend/
├── app/
│   ├── layout.tsx            # Root layout
│   ├── page.tsx              # Landing / main chat page
│   └── api/                  # (opsional) BFF proxy
├── components/
│   ├── ChatInput.tsx         # Input natural language query
│   ├── SQLPreview.tsx        # Tampilkan generated SQL + tombol execute
│   ├── ResultTable.tsx       # Tabel hasil query
│   ├── SchemaViewer.tsx      # Sidebar: tampilkan schema DB
│   ├── QueryHistory.tsx      # Riwayat query sebelumnya
│   └── ErrorBanner.tsx       # Error handling UI
├── lib/
│   ├── api.ts                # API client (fetch wrapper)
│   └── types.ts              # TypeScript interfaces
└── public/
```

**Fitur UI:**

- Input box chat-style untuk mengetik pertanyaan
- Preview SQL yang di-generate (editable sebelum execute)
- Tabel hasil query dengan pagination
- Schema browser sidebar (user bisa lihat tabel & kolom DB)
- Query history panel
- Dark/light mode toggle

### 4.2 Backend (FastAPI)

```
backend/
├── main.py                   # FastAPI app entry point
├── config.py                 # Environment config (API key, DB URL, dll)
├── routers/
│   ├── query.py              # POST /api/query  — main endpoint
│   ├── schema.py             # GET  /api/schema — introspect DB schema
│   └── history.py            # GET  /api/history — query history
├── services/
│   ├── llm_service.py        # Komunikasi dengan GLM API
│   ├── sql_generator.py      # Prompt engineering + SQL generation
│   ├── sql_executor.py       # Execute SQL query ke DB (read-only)
│   └── schema_inspector.py   # Introspect DB schema via SQLAlchemy
├── models/
│   ├── request.py            # Pydantic request models
│   └── response.py           # Pydantic response models
├── middleware/
│   └── security.py           # Rate limiting, input sanitization
├── .env                      # GLM_API_KEY, DATABASE_URL
└── requirements.txt
```

### 4.3 GLM API Integration

```python
# services/llm_service.py — Pseudocode

class GLMService:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    async def generate_sql(self, user_question: str, schema_context: str) -> str:
        prompt = self._build_prompt(user_question, schema_context)
        response = await httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": "glm-4",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1  # low temp untuk SQL accuracy
            }
        )
        return self._extract_sql(response.json())
```

**System Prompt Strategy:**

```
Kamu adalah SQL expert. Diberikan schema database dan pertanyaan user,
generate SQL query yang valid untuk PostgreSQL.

Rules:
- Hanya gunakan tabel dan kolom yang ada di schema
- Gunakan SELECT saja (tidak boleh INSERT/UPDATE/DELETE/DROP)
- Berikan SQL saja tanpa penjelasan
- Gunakan alias yang readable
```

## 5. RAG Pipeline (Retrieval-Augmented Generation)

### 5.1 Mengapa RAG?

Tanpa RAG, kita harus memasukkan **seluruh schema database** ke dalam prompt setiap kali user bertanya. Ini bermasalah ketika:
- Database punya 50+ tabel — context window LLM terbatas & mahal
- Banyak kolom yang tidak relevan — noise menurunkan akurasi SQL
- Butuh konteks tambahan (relasi antar tabel, business logic, contoh query)

**Dengan RAG**, kita hanya retrieve schema & metadata yang **relevan** dengan pertanyaan user.

### 5.2 RAG Architecture

```
User Question
      │
      ▼
┌─────────────────┐
│  1. Embedding   │──── GLM Embedding API
│     Question    │     (embedding-3)
└────────┬────────┘
         │ vector
         ▼
┌─────────────────┐     ┌──────────────────────────┐
│  2. Vector      │────▶│  ChromaDB / FAISS        │
│     Search      │     │  (Vector Store)          │
│                 │◀────│                          │
└────────┬────────┘     │  Indexed:                │
         │              │  - Table descriptions    │
         │              │  - Column metadata       │
         │              │  - Relationship info     │
         │              │  - Sample queries (few-shot)│
         │              │  - Business glossary     │
         │              └──────────────────────────┘
         │ top-k relevant chunks
         ▼
┌─────────────────┐
│  3. Prompt      │
│     Assembly    │
│                 │
│  System Prompt  │
│  + Retrieved    │
│    Schema       │
│  + Few-shot     │
│    Examples     │
│  + User Question│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. GLM API     │──── Generate SQL
│     (LLM)       │
└────────┬────────┘
         │
         ▼
   Generated SQL
```

### 5.3 Knowledge Base: Apa yang Di-index?

Vector store menyimpan beberapa tipe dokumen yang di-embed:

```
knowledge_base/
├── schema/
│   ├── tables.jsonl          # Deskripsi setiap tabel
│   ├── columns.jsonl         # Metadata kolom (type, constraint, deskripsi)
│   └── relationships.jsonl   # Foreign keys & relasi antar tabel
├── glossary/
│   └── business_terms.jsonl  # Mapping istilah bisnis → kolom/tabel
├── examples/
│   └── few_shot_queries.jsonl # Contoh pasangan question → SQL
└── docs/
    └── query_patterns.jsonl  # Pattern query umum (aggregation, join, dll)
```

**Contoh dokumen yang di-embed:**

```json
// tables.jsonl
{
  "doc_type": "table",
  "table_name": "orders",
  "description": "Menyimpan semua transaksi pembelian customer. Setiap row = 1 order.",
  "columns_summary": "id, customer_id (FK→customers), product_id (FK→products), quantity, total_price, status, created_at",
  "common_queries": "total penjualan, order terbanyak, revenue per bulan"
}

// business_terms.jsonl
{
  "doc_type": "glossary",
  "term": "revenue",
  "definition": "Total pendapatan = SUM(orders.total_price) WHERE status = 'completed'",
  "related_tables": ["orders"],
  "sql_pattern": "SUM(total_price) FILTER (WHERE status = 'completed')"
}

// few_shot_queries.jsonl
{
  "doc_type": "example",
  "question": "Siapa 5 customer dengan spending terbanyak bulan ini?",
  "sql": "SELECT c.name, SUM(o.total_price) AS total_spent FROM customers c JOIN orders o ON c.id = o.customer_id WHERE o.created_at >= DATE_TRUNC('month', CURRENT_DATE) AND o.status = 'completed' GROUP BY c.name ORDER BY total_spent DESC LIMIT 5",
  "tables_used": ["customers", "orders"]
}
```

### 5.4 Indexing Pipeline

```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│ DB Schema    │     │  Chunking &   │     │  Embedding   │
│ Introspection│────▶│  Enrichment   │────▶│  + Store     │
│ (SQLAlchemy) │     │               │     │  (ChromaDB)  │
└──────────────┘     └───────────────┘     └──────────────┘
      │                     │                      │
  Auto-extract         Add deskripsi          GLM Embedding
  tables, columns,     bisnis, contoh         API → vectors
  FK, constraints      query, glossary        → ChromaDB
```

**Kapan re-index:**
- Saat aplikasi pertama kali start (initial sync)
- Saat ada perubahan schema (migration detected)
- Manual trigger via `POST /api/index/rebuild`

### 5.5 Retrieval Strategy

```python
# services/rag_service.py — Pseudocode

class RAGService:
    def __init__(self, vector_store, embedding_service):
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    async def retrieve_context(self, question: str, top_k: int = 10) -> RAGContext:
        # 1. Embed pertanyaan user
        query_vector = await self.embedding_service.embed(question)

        # 2. Retrieve relevant documents dari vector store
        results = self.vector_store.query(
            query_vector=query_vector,
            n_results=top_k,
            where={"doc_type": {"$in": ["table", "column", "glossary", "example"]}}
        )

        # 3. Re-rank: prioritaskan table > glossary > example
        ranked = self._rerank(results)

        # 4. Build context string
        return RAGContext(
            relevant_tables=self._extract_tables(ranked),
            relevant_columns=self._extract_columns(ranked),
            few_shot_examples=self._extract_examples(ranked),
            glossary_terms=self._extract_glossary(ranked)
        )
```

### 5.6 Prompt Assembly (setelah retrieval)

```python
# services/sql_generator.py

SYSTEM_PROMPT = """Kamu adalah SQL expert untuk PostgreSQL.

Rules:
- Hanya gunakan tabel dan kolom yang diberikan di <schema>
- Hanya SELECT (tidak boleh INSERT/UPDATE/DELETE/DROP)
- Berikan SQL saja tanpa penjelasan
- Gunakan alias yang readable
"""

def build_prompt(question: str, rag_context: RAGContext) -> str:
    return f"""<schema>
{rag_context.relevant_tables_as_ddl()}
</schema>

<glossary>
{rag_context.glossary_terms_as_text()}
</glossary>

<examples>
{rag_context.few_shot_examples_as_text()}
</examples>

<question>
{question}
</question>

Berikan SQL query yang menjawab pertanyaan di atas:"""
```

### 5.7 Updated Tech Stack (RAG)

| Komponen            | Technology             | Alasan                                            |
| ------------------- | ---------------------- | ------------------------------------------------- |
| **Vector Store**    | ChromaDB               | Lightweight, Python-native, mudah di-embed di app |
| **Embedding Model** | GLM Embedding API      | Konsisten dengan LLM yang sama (1 vendor)         |
| **Chunking**        | Custom per doc_type    | Schema butuh chunking berbeda dari free-text      |
| **Re-ranking**      | Rule-based + semantic  | Prioritas: table schema > glossary > few-shot     |

### 5.8 Updated Backend Structure (dengan RAG)

```
backend/
├── main.py
├── config.py
├── routers/
│   ├── query.py
│   ├── schema.py
│   ├── history.py
│   └── index.py              # POST /api/index/rebuild — trigger re-index
├── services/
│   ├── llm_service.py        # Komunikasi dengan GLM API
│   ├── embedding_service.py  # NEW: embed text via GLM Embedding API
│   ├── rag_service.py        # NEW: retrieve relevant context
│   ├── indexing_service.py   # NEW: index schema + docs ke vector store
│   ├── sql_generator.py      # Prompt assembly (pakai RAG context)
│   ├── sql_executor.py
│   └── schema_inspector.py
├── knowledge_base/            # NEW: source documents untuk indexing
│   ├── glossary/
│   └── examples/
├── models/
├── middleware/
├── .env
└── requirements.txt          # + chromadb, numpy
```

### 5.9 Updated Data Flow (dengan RAG)

```
1. User ketik pertanyaan di Chat Input
        │
        ▼
2. Frontend POST /api/query { question: "..." }
        │
        ▼
3. RAG Retrieval:
   a. Embed pertanyaan user → query vector
   b. Search ChromaDB → top-k relevant chunks
   c. Extract: relevant tables, columns, glossary, few-shot examples
        │
        ▼
4. Prompt Assembly:
   - System prompt (rules)
   - Retrieved schema (hanya tabel relevan, bukan seluruh DB)
   - Glossary terms (mapping istilah bisnis)
   - Few-shot examples (contoh question→SQL serupa)
   - User question
        │
        ▼
5. GLM API generate SQL
        │
        ▼
6. Validasi SQL (read-only check)
        │
        ▼
7. Execute SQL ke PostgreSQL
        │
        ▼
8. Return { sql, results, retrieved_context } ke Frontend
        │
        ▼
9. Frontend render:
   - SQL Preview (editable)
   - Result Table
   - Context panel (tabel mana yang dipakai, confidence)
```

## 6. API Endpoints

### `POST /api/query`

Request:
```json
{
  "question": "Tampilkan 10 customer dengan total order terbanyak",
  "execute": true
}
```

Response:
```json
{
  "question": "Tampilkan 10 customer dengan total order terbanyak",
  "generated_sql": "SELECT c.name, COUNT(o.id) AS total_orders FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name ORDER BY total_orders DESC LIMIT 10",
  "results": {
    "columns": ["name", "total_orders"],
    "rows": [
      ["Budi", 42],
      ["Siti", 38]
    ],
    "row_count": 10
  },
  "execution_time_ms": 120
}
```

### `GET /api/schema`

Response:
```json
{
  "tables": [
    {
      "name": "customers",
      "columns": [
        {"name": "id", "type": "INTEGER", "primary_key": true},
        {"name": "name", "type": "VARCHAR(255)"},
        {"name": "email", "type": "VARCHAR(255)"}
      ]
    }
  ]
}
```

### `GET /api/history`

Response:
```json
{
  "queries": [
    {
      "id": 1,
      "question": "...",
      "sql": "...",
      "timestamp": "2026-03-28T10:00:00Z"
    }
  ]
}
```

## 7. Security

| Concern              | Mitigasi                                                 |
| -------------------- | -------------------------------------------------------- |
| SQL Injection        | Validasi SQL hanya SELECT; jalankan di read-only DB role  |
| API Key exposure     | GLM API key hanya di backend (.env), tidak di frontend   |
| DDoS / abuse         | Rate limiting per IP (misal 20 req/menit)                |
| Data leakage         | Batasi result set (max 1000 rows)                        |
| Prompt injection     | Sanitize user input, strict system prompt                |

**Read-Only DB User:**
```sql
CREATE USER text_to_sql_reader WITH PASSWORD '...';
GRANT CONNECT ON DATABASE mydb TO text_to_sql_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO text_to_sql_reader;
```

## 8. Environment Variables

```env
# Backend (.env)
GLM_API_KEY=your-glm-api-key-here
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
GLM_MODEL=glm-4
GLM_EMBEDDING_MODEL=embedding-3
DATABASE_URL=postgresql://text_to_sql_reader:password@localhost:5432/mydb
CHROMA_PERSIST_DIR=./chroma_data
RAG_TOP_K=10
MAX_RESULT_ROWS=1000
RATE_LIMIT_PER_MINUTE=20

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 9. Deployment

```
                    ┌──────────────┐
                    │   Nginx /    │
                    │   Reverse    │
   User ──────────▶│   Proxy      │
                    │   (port 80)  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼                         ▼
     ┌────────────────┐       ┌────────────────┐
     │  Frontend      │       │  Backend       │
     │  Next.js       │       │  FastAPI       │
     │  (port 3000)   │       │  (port 8000)   │
     └────────────────┘       └───────┬────────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │  PostgreSQL  │
                              │  (port 5432) │
                              └──────────────┘
```

**Docker Compose (Production):**
- `frontend` — Next.js container
- `backend` — FastAPI + Uvicorn container
- `db` — PostgreSQL container
- `nginx` — Reverse proxy

## 10. Development Roadmap

### Phase 1 — MVP
- [ ] Setup project structure (frontend + backend)
- [ ] Integrasi GLM API (generate SQL dari natural language)
- [ ] Basic UI: input → SQL preview → execute → result table
- [ ] Schema introspection endpoint
- [ ] Read-only SQL execution

### Phase 2 — RAG Pipeline
- [ ] Setup ChromaDB vector store
- [ ] Indexing pipeline (schema → embedding → ChromaDB)
- [ ] Embedding service (GLM Embedding API)
- [ ] RAG retrieval service (query → top-k relevant context)
- [ ] Knowledge base: business glossary + few-shot examples
- [ ] Prompt assembly dengan RAG context
- [ ] Re-index endpoint (`POST /api/index/rebuild`)

### Phase 3 — Enhancement
- [ ] Query history (persist di DB)
- [ ] Schema browser sidebar
- [ ] SQL editing sebelum execute
- [ ] Error handling & user-friendly error messages
- [ ] Loading states & streaming response
- [ ] Context panel (tampilkan tabel yang di-retrieve RAG)

### Phase 4 — Polish
- [ ] Dark/light mode
- [ ] Export hasil ke CSV
- [ ] Multi-database support
- [ ] Authentication (jika diperlukan)
- [ ] Deploy ke cloud (Docker Compose)
- [ ] Feedback loop: user bisa rate hasil SQL → improve few-shot examples
