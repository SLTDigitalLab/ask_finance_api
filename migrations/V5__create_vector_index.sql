CREATE TABLE IF NOT EXISTS vector_index (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    collection_id VARCHAR(255),
    collection_name VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP 
);