CREATE TABLE IF NOT EXISTS token_cost_usage (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    token_cost INTEGER,
    usage_cost Numeric(10,5)
);