CREATE TABLE collection (
    id SERIAL PRIMARY KEY,
    collection_id TEXT UNIQUE,
    collection_name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
