CREATE TABLE IF NOT EXISTS api_keys (
    api_key VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    user_id VARCHAR(255),
    allowed_origins TEXT[],
    scope json,
    expire_ts TIMESTAMP,
    disabled BOOLEAN DEFAULT FALSE,
    date_disabled TIMESTAMP DEFAULT NULL,
    last_used TIMESTAMP DEFAULT NULL,
    created_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    FOREIGN KEY(user_id) REFERENCES users(id)
);