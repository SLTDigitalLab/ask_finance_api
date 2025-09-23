CREATE OR REPLACE FUNCTION insert_token_for_users()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO token_cost_usage (user_id, token_cost, usage_cost)
    VALUES (NEW.id, 0, 0);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_after_insert_user
AFTER INSERT ON users
FOR EACH ROW
EXECUTE FUNCTION insert_token_for_users();