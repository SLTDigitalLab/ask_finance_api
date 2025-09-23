CREATE TABLE IF NOT EXISTS authenticated_aws_users (
  uuid uuid PRIMARY KEY,
  user_id VARCHAR(255),
  type VARCHAR(255) NOT NULL,
  aws_access_key_id VARCHAR(255) NOT NULL,
  aws_secret_access_key VARCHAR(255) NOT NULL,
  bucket_name VARCHAR(255) NOT NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);