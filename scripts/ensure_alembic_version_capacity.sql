CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(128) NOT NULL PRIMARY KEY
);

ALTER TABLE alembic_version
    ALTER COLUMN version_num TYPE VARCHAR(128);
