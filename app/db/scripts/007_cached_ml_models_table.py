from db.psql_connector import DB, default_config

"""
INSERT INTO cached_ml_models 
(id, user_id, model_path, features, targets, algo_type, 
types_map, project_id, train_accu, test_accu, dataset, permanent_save, 
created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *
"""


def createCachedMLModelsTable():
    db = DB(default_config())
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS cached_ml_models (
            id VARCHAR(255) PRIMARY KEY, 
            user_id VARCHAR(255),
            model_path VARCHAR(1024), 
            features TEXT[],
            targets TEXT[],
            algo_type VARCHAR(255), 
            types_map json,
            project_id VARCHAR(255), 
            train_accu numeric,
            test_accu numeric,
            dataset VARCHAR(512) DEFAULT NULL,
            hyper_params json DEFAULT NULL,
            permanent_save BOOLEAN DEFAULT FALSE,
            created_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            updated_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
    """
    )
    result = db.fetchone()
    return result


print(createCachedMLModelsTable())
