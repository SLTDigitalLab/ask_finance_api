
-- payments table (with package_name)
CREATE TABLE IF NOT EXISTS payments (
    payment_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id),  -- Foreign key to link with users
    order_id VARCHAR(255),  -- The order_id you send to PayHere
    tier VARCHAR(255),   -- Store the name of the package being purchased
    amount NUMERIC(10, 2),
    currency VARCHAR(3),
    status VARCHAR(20)
);  