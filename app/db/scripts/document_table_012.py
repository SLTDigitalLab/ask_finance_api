from db.psql_connector import DB, default_config

def createDocumentTable():
    db = DB(default_config())
    cursor = db.conn.cursor()

    cursor.execute(
        """
        CREATE TABLE documents (
            id SERIAL PRIMARY KEY,
            document_id UUID NOT NULL,
            collection_id TEXT,
            chunk_index INT,
            total_chunks INT,
            content TEXT,
            source TEXT,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );

        """
    )

    db.conn.commit()  
    print("document table created (if not already exists)")
    return True

if __name__ == "__main__":
    createDocumentTable()