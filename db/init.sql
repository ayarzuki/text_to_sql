-- Create read-only user for text-to-sql app
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'text_to_sql_reader') THEN
        CREATE ROLE text_to_sql_reader WITH LOGIN PASSWORD 'reader_password';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE texttosql TO text_to_sql_reader;

-- Grant read-only access on all current and future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO text_to_sql_reader;

-- Sample tables for demo/testing
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant SELECT on the sample tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO text_to_sql_reader;

-- Seed sample data
INSERT INTO customers (name, email, city) VALUES
    ('Budi Santoso', 'budi@example.com', 'Jakarta'),
    ('Siti Rahayu', 'siti@example.com', 'Bandung'),
    ('Agus Wijaya', 'agus@example.com', 'Surabaya'),
    ('Dewi Lestari', 'dewi@example.com', 'Yogyakarta'),
    ('Rizky Pratama', 'rizky@example.com', 'Jakarta')
ON CONFLICT DO NOTHING;

INSERT INTO products (name, category, price, stock) VALUES
    ('Laptop Pro X', 'Electronics', 15000000.00, 50),
    ('Wireless Mouse', 'Electronics', 250000.00, 200),
    ('Office Chair', 'Furniture', 3500000.00, 30),
    ('Standing Desk', 'Furniture', 5000000.00, 15),
    ('USB-C Hub', 'Electronics', 450000.00, 100)
ON CONFLICT DO NOTHING;

INSERT INTO orders (customer_id, product_id, quantity, total_price, status) VALUES
    (1, 1, 1, 15000000.00, 'completed'),
    (1, 2, 2, 500000.00, 'completed'),
    (2, 3, 1, 3500000.00, 'completed'),
    (3, 4, 1, 5000000.00, 'pending'),
    (4, 5, 3, 1350000.00, 'completed'),
    (5, 1, 1, 15000000.00, 'completed'),
    (2, 2, 1, 250000.00, 'completed'),
    (3, 3, 2, 7000000.00, 'completed')
ON CONFLICT DO NOTHING;
