from db.psql_connector import DB, default_config

def createAskDocument():
    db = DB(default_config())
    cursor = db.conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ask_hr_history (
            id SERIAL PRIMARY KEY,
            chat_id UUID NOT NULL,
            domain TEXT NOT NULL,
            role TEXT NOT NULL,       
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT NOW()
        )
        """
    )

    db.conn.commit()  
    print("ask_hr_history table created (if not already exists)")
    return True

if __name__ == "__main__":
    createAskDocument()