CREATE OR REPLACE FUNCTION maintain_chat_history_limit()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if there are more than 10 chat sessions for the same chat ID
    IF (SELECT COUNT(*) FROM chat_history WHERE chat_id = NEW.chat_id) > 10 THEN
        -- Delete the oldest entries exceeding the limit of 10
        DELETE FROM chat_history
        WHERE ctid IN (
            SELECT ctid FROM chat_history
            WHERE chat_id = NEW.chat_id
            ORDER BY timestamp ASC
            LIMIT (SELECT COUNT(*) - 10 FROM chat_history WHERE chat_id = NEW.chat_id)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_after_insert_chat_history
AFTER INSERT ON chat_history
FOR EACH ROW
EXECUTE FUNCTION maintain_chat_history_limit();