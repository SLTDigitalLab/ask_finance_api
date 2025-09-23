from db.psql_connector import DB, default_config

def createCollectionTable():
    db = DB(default_config())
    cursor = db.conn.cursor()

    cursor.execute(
        """
        CREATE TABLE collection (
            id SERIAL PRIMARY KEY,
            collection_id TEXT UNIQUE,
            collection_name TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        """
    )

    db.conn.commit()  
    print("collection table created (if not already exists)")
    return True

if __name__ == "__main__":
    createCollectionTable()