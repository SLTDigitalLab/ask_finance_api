CREATE TABLE scheduler_logs (
    log_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    function_name VARCHAR(255),
    status VARCHAR(255),  -- 'success' or 'error'
    user_id VARCHAR(255),  -- user id
    details TEXT
);