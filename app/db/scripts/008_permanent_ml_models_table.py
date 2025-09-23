from db.psql_connector import DB, default_config


def createPermanentMLModelsTable():
    db = DB(default_config())
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS permanent_ml_models (
            id VARCHAR(255) PRIMARY KEY, 
            model_name VARCHAR(255), 
            model_path VARCHAR(1024), 
            user_id VARCHAR(255),
            algo_type VARCHAR(255), 
            is_public BOOLEAN DEFAULT FALSE,
            features TEXT[],
            targets TEXT[],
            types_map json,
            project_id VARCHAR(255), 
            train_accu numeric,
            test_accu numeric,
            dataset VARCHAR(512) DEFAULT NULL,
            hyper_params json DEFAULT NULL,
            short_desc VARCHAR(1024) DEFAULT NULL, 
            long_desc TEXT DEFAULT NULL,
            created_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            updated_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
    """
    )
    result = db.fetchone()
    return result


print(createPermanentMLModelsTable())
