from db.psql_connector import DB, default_config

def createLinkTable():
    db = DB(default_config())
    cursor = db.conn.cursor()

    cursor.execute(
        """
        CREATE TABLE link (
            link_id VARCHAR PRIMARY KEY,
            collection_id VARCHAR REFERENCES collection(collection_id),
            url TEXT,
            title TEXT,
            description TEXT,
            created_at TIMESTAMP
        );

        """
    )

    db.conn.commit()  
    print("Link table created (if not already exists)")
    return True

if __name__ == "__main__":
    createLinkTable()