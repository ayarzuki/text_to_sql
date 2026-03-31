import os
import sys
import sqlite3
import tempfile
import pytest
from httpx import AsyncClient, ASGITransport

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Override env before importing app
os.environ["GLM_API_KEY"] = "test-key"
os.environ["GLM_BASE_URL"] = "https://api.z.ai/api/paas/v4"
os.environ["GLM_MODEL"] = "glm-4.5"
os.environ["GLM_EMBEDDING_MODEL"] = "embedding-3"


@pytest.fixture(scope="session")
def test_db():
    """Create a temporary SQLite database with sample data."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = tmp.name

    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            city TEXT
        );
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0
        );
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(id),
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'pending'
        );

        INSERT INTO customers VALUES (1, 'Budi', 'budi@test.com', 'Jakarta');
        INSERT INTO customers VALUES (2, 'Siti', 'siti@test.com', 'Bandung');
        INSERT INTO products VALUES (1, 'Laptop', 'Electronics', 15000000, 10);
        INSERT INTO products VALUES (2, 'Mouse', 'Electronics', 250000, 50);
        INSERT INTO orders VALUES (1, 1, 1, 1, 15000000, 'completed');
        INSERT INTO orders VALUES (2, 1, 2, 2, 500000, 'completed');
        INSERT INTO orders VALUES (3, 2, 1, 1, 15000000, 'pending');
    """)
    conn.commit()
    conn.close()

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    yield db_path

    try:
        os.unlink(db_path)
    except PermissionError:
        pass  # Windows file lock — will be cleaned up by OS


@pytest.fixture
def db_url(test_db):
    return f"sqlite:///{test_db}"


@pytest.fixture
def chroma_dir():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
async def client(test_db, chroma_dir):
    """Create a test client with real SQLite DB."""
    os.environ["DATABASE_URL"] = f"sqlite:///{test_db}"
    os.environ["CHROMA_PERSIST_DIR"] = chroma_dir

    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
