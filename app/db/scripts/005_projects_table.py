from db.psql_connector import DB, default_config


def createProjectsTable():
    db = DB(default_config())
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            is_private BOOLEAN DEFAULT TRUE,
            user_id VARCHAR(255) NOT NULL,
            algo_type VARCHAR(255) NOT NULL,
            algo_selected VARCHAR(255) NOT NULL,
            shared_type VARCHAR(10) DEFAULT NULL,
            shared_with TEXT DEFAULT NULL,
            dataset_name TEXT DEFAULT NULL,
            model_path TEXT DEFAULT NULL,
            model_type VARCHAR(10) DEFAULT NULL,
            encoder_path TEXT DEFAULT NULL,
            encoder_type VARCHAR(10) DEFAULT NULL,
            is_community_model BOOLEAN DEFAULT FALSE,
            community_model_url VARCHAR(255) DEFAULT NULL,
            exposer_id VARCHAR(255) DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES user(id),
            FOREIGN KEY(exposer_id) REFERENCES exposer(id)
        )
    """
    )
    result = db.fetchone()
    return result


print(createProjectsTable())
