from db.psql_connector import DB, default_config


def createExposerTable():
    db = DB(default_config())
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id VARCHAR(255) PRIMARY KEY,
            endpoint VARCHAR(512) NOT NULL,
            req_struct json NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    result = db.fetchone()
    return result


print(createExposerTable())
