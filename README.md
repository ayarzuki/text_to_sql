# Text-to-SQL

Aplikasi web AI-powered yang mengkonversi pertanyaan bahasa natural menjadi SQL query menggunakan GLM (via Z.ai API) dengan RAG (Retrieval-Augmented Generation) pipeline.

## Architecture

```
User (Browser)
      │
      ▼
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Nginx   │────▶│   Next.js    │     │   FastAPI     │
│  :80     │     │   :3000      │     │   :8000       │
└──────────┘     └──────────────┘     └──────┬───────┘
      │                                      │
      │         /api/* ─────────────────────▶│
      │                                      │
      │                               ┌──────┴───────┐
      │                               │              │
      │                          ┌────▼────┐  ┌──────▼──────┐
      │                          │ ChromaDB│  │ GLM API     │
      │                          │ (RAG)   │  │ (Z.ai)      │
      │                          └─────────┘  └─────────────┘
      │                               │
      │                          ┌────▼────┐
      │                          │PostgreSQL│
      │                          │ :5432    │
      └──────────────────────────┴──────────┘
```

### Data Flow

1. User mengetik pertanyaan natural language di web UI
2. Backend menerima pertanyaan via `POST /api/query`
3. **RAG Retrieval**: Embed pertanyaan → cari di ChromaDB → ambil schema tabel, glossary, dan few-shot examples yang relevan
4. **Prompt Assembly**: Gabungkan system prompt + retrieved context + pertanyaan user
5. **GLM API**: Generate SQL query dari prompt
6. **Validasi**: Pastikan SQL hanya SELECT (block INSERT/UPDATE/DELETE/DROP)
7. **Execute**: Jalankan SQL ke database, return hasilnya
8. Frontend menampilkan SQL yang di-generate + tabel hasil

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, React 18, Tailwind CSS |
| Backend | FastAPI, Python 3.10+ |
| LLM | GLM-4.5 via Z.ai API (OpenAI-compatible) |
| RAG Vector Store | ChromaDB |
| Database | PostgreSQL (Docker) / SQLite (local dev) |
| Reverse Proxy | Nginx |
| Container | Docker Compose |

## Project Structure

```
text-to-sql/
├── backend/
│   ├── main.py                     # FastAPI entry point, lifespan, CORS
│   ├── config.py                   # Pydantic Settings (.env loader)
│   ├── routers/
│   │   ├── query.py                # POST /api/query — main text-to-SQL endpoint
│   │   ├── schema.py               # GET  /api/schema — database schema introspection
│   │   ├── history.py              # GET  /api/history — query history
│   │   └── index.py                # POST /api/index/rebuild — rebuild RAG index
│   ├── services/
│   │   ├── llm_service.py          # GLM API client (chat completions)
│   │   ├── embedding_service.py    # GLM Embedding API client
│   │   ├── rag_service.py          # RAG retrieval (vector search + keyword fallback)
│   │   ├── indexing_service.py     # Index schema & knowledge base → ChromaDB
│   │   ├── sql_generator.py        # Prompt assembly + SQL validation
│   │   ├── sql_executor.py         # Execute SQL (read-only)
│   │   ├── schema_inspector.py     # SQLAlchemy introspection → DDL
│   │   └── history_store.py        # In-memory query history
│   ├── models/
│   │   ├── request.py              # Pydantic request models
│   │   └── response.py             # Pydantic response models
│   ├── middleware/
│   │   └── security.py             # Rate limiting (slowapi)
│   ├── knowledge_base/
│   │   ├── glossary/               # Business term definitions (JSONL)
│   │   └── examples/               # Few-shot query examples (JSONL)
│   ├── tests/                      # Pytest test suite (59 tests)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── layout.tsx              # Root layout
│   │   ├── page.tsx                # Main page (chat UI + results)
│   │   └── globals.css             # Tailwind + custom styles
│   ├── components/
│   │   ├── ChatInput.tsx           # Natural language input box
│   │   ├── SQLPreview.tsx          # Generated SQL display + copy
│   │   ├── ResultTable.tsx         # Query results data table
│   │   ├── SchemaViewer.tsx        # Database schema browser sidebar
│   │   ├── QueryHistory.tsx        # Query history list
│   │   └── ErrorBanner.tsx         # Error display
│   ├── lib/
│   │   ├── api.ts                  # API client (fetch wrapper)
│   │   └── types.ts                # TypeScript interfaces
│   ├── __tests__/                  # Jest test suite (22 tests)
│   ├── Dockerfile
│   └── package.json
├── nginx/
│   ├── nginx.conf                  # Reverse proxy config
│   └── Dockerfile
├── db/
│   └── init.sql                    # PostgreSQL init: schema + seed data
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/query` | Generate SQL dari pertanyaan + execute |
| `GET` | `/api/schema` | Lihat schema database (tabel & kolom) |
| `GET` | `/api/history` | Riwayat query sebelumnya |
| `POST` | `/api/index/rebuild` | Rebuild RAG index |
| `GET` | `/docs` | Swagger UI (auto-generated) |

## Getting Started

### Prerequisites

- **Docker** (recommended) atau:
  - Python 3.10+
  - Node.js 20+
  - PostgreSQL 16 (atau SQLite untuk dev)
- **API Key** dari [Z.ai](https://z.ai) atau [ZhipuAI](https://open.bigmodel.cn)

### Setup Environment

```bash
# Copy dan edit file environment
cp .env.example .env
```

Edit `.env` dan isi `GLM_API_KEY` dengan API key Anda:

```env
GLM_API_KEY=your-api-key-here
GLM_BASE_URL=https://api.z.ai/api/paas/v4
GLM_MODEL=glm-4.5
```

---

### Option 1: Run with Docker (Recommended)

```bash
# Build dan jalankan semua service
docker compose up --build -d

# Cek status
docker compose ps

# Lihat logs
docker compose logs -f backend
```

Akses aplikasi:
- **Web UI**: http://localhost
- **API Docs**: http://localhost/docs
- **Backend langsung**: http://localhost:8000
- **Database**: localhost:5432

Stop semua service:
```bash
docker compose down
```

---

### Option 2: Run Locally (Development)

#### 1. Database

Pilih salah satu:

**SQLite (simple, no setup):**
```bash
cd backend
python -c "
import sqlite3
conn = sqlite3.connect('test.db')
conn.executescript(open('../db/init.sql').read().replace('SERIAL','INTEGER').replace('DECIMAL(10, 2)','REAL').replace('VARCHAR(255)','TEXT').replace('VARCHAR(100)','TEXT').replace('VARCHAR(20)','TEXT').replace('DEFAULT CURRENT_TIMESTAMP',''))
conn.commit()
conn.close()
print('SQLite database created: test.db')
"
```

**PostgreSQL:**
```bash
# Jalankan PostgreSQL via Docker
docker run -d --name texttosql-db \
  -e POSTGRES_DB=texttosql \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -v ./db/init.sql:/docker-entrypoint-initdb.d/init.sql \
  postgres:16-alpine
```

#### 2. Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Jalankan (SQLite)
DATABASE_URL="sqlite:///test.db" uvicorn main:app --reload --port 8000

# Jalankan (PostgreSQL)
uvicorn main:app --reload --port 8000
```

Backend berjalan di http://localhost:8000.
API docs di http://localhost:8000/docs.

#### 3. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Jalankan dev server
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Frontend berjalan di http://localhost:3000.

---

## Testing

### Backend Tests (59 tests)

```bash
cd backend
pip install pytest pytest-asyncio
python -m pytest tests/ -v -p no:recording
```

Test coverage:
- `test_api_endpoints.py` — API endpoint HTTP tests
- `test_schema_inspector.py` — Database schema introspection
- `test_sql_generator.py` — SQL validation & extraction (block DROP/DELETE/INSERT/UPDATE)
- `test_sql_executor.py` — SQL execution & result formatting
- `test_history_store.py` — Query history CRUD
- `test_indexing_service.py` — ChromaDB indexing pipeline
- `test_rag_service.py` — RAG retrieval & context building
- `test_models.py` — Pydantic model validation

### Frontend Tests (22 tests)

```bash
cd frontend
npm install
npm test
```

Test coverage:
- `api.test.ts` — API client (fetch mock)
- `components.test.tsx` — React component rendering & interactions
- `types.test.ts` — TypeScript interface validation

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `GLM_API_KEY` | — | API key Z.ai / ZhipuAI (required) |
| `GLM_BASE_URL` | `https://api.z.ai/api/paas/v4` | GLM API base URL |
| `GLM_MODEL` | `glm-4.5` | Model name (`glm-4.5`, `glm-4.7`, `glm-5`) |
| `GLM_EMBEDDING_MODEL` | `embedding-3` | Embedding model name |
| `DATABASE_URL` | `postgresql://...` | Database connection string |
| `CHROMA_PERSIST_DIR` | `/app/chroma_data` | ChromaDB storage path |
| `RAG_TOP_K` | `10` | Jumlah dokumen RAG yang di-retrieve |
| `MAX_RESULT_ROWS` | `1000` | Max rows per query result |
| `RATE_LIMIT_PER_MINUTE` | `20` | API rate limit per IP |

## Security

- SQL query di-validasi: hanya `SELECT` yang diizinkan (block `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, `REVOKE`)
- API key GLM hanya ada di backend (tidak exposed ke frontend)
- Rate limiting per IP (20 req/menit default)
- Database user read-only (production)
- Result set dibatasi (max 1000 rows default)
