CREATE TABLE IF NOT EXISTS collection_images (
    id VARCHAR(255) PRIMARY KEY,
    collection_id VARCHAR(255),
    image_path VARCHAR(255)
);