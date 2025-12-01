-- Quick Fix: Grant PostgreSQL Permissions to sre_user
-- Run this directly with psql if you have postgres password

-- Connect to sre_agent_db database
\c sre_agent_db

-- Grant schema usage
GRANT USAGE ON SCHEMA public TO sre_user;

-- Grant permissions on all existing tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sre_user;

-- Grant permissions on sequences
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sre_user;

-- Grant permissions on future tables (for migrations)
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sre_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public 
  GRANT USAGE, SELECT ON SEQUENCES TO sre_user;

-- Verify users table permissions
\dp users

-- Test query as sre_user
SET ROLE sre_user;
SELECT COUNT(*) FROM users;
RESET ROLE;

\echo '✅ Permissions granted successfully!'
