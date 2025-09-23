CREATE TABLE user_api_keys (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    api_key VARCHAR(255) REFERENCES api_keys(api_key) ON DELETE CASCADE,
    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, api_key) 
);