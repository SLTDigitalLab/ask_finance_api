from db.psql_connector import DB, default_config

def createVirtualKandyChatTableNew():
    db = DB(default_config())
    cursor = db.conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS virtual_kandy_chat_history_new (
            id SERIAL PRIMARY KEY,
            chat_id VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,  
            message TEXT NOT NULL,
            project VARCHAR(255) DEFAULT 'virtual-kandy',
            metadata JSON DEFAULT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    db.conn.commit()  
    print("virtual_kandy_chat_history_new table created (if not already exists)")
    return True

if __name__ == "__main__":
    createVirtualKandyChatTableNew()