CREATE TABLE IF NOT EXISTS pdfs (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id),
    collection_id VARCHAR(255),
    file_path VARCHAR(255),
    file_name VARCHAR(255)
);