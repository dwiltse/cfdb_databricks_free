-- Unity Catalog Setup for CFDB Project
-- Run this in your Databricks workspace before creating the DLT pipeline

-- =====================================================
-- CREATE CATALOG AND SCHEMAS
-- =====================================================

-- Create the main catalog
CREATE CATALOG IF NOT EXISTS cfdb_dev
COMMENT 'College Football Database development environment';

-- Create bronze schema for raw data ingestion
CREATE SCHEMA IF NOT EXISTS cfdb_dev.bronze
COMMENT 'Bronze layer - raw data from S3 external location';

-- Create silver schema for cleaned and standardized data
CREATE SCHEMA IF NOT EXISTS cfdb_dev.silver
COMMENT 'Silver layer - cleaned and standardized data for analytics';

-- Create gold schema for business logic and ML features
CREATE SCHEMA IF NOT EXISTS cfdb_dev.gold
COMMENT 'Gold layer - business metrics and ML-ready feature sets';

-- =====================================================
-- GRANTS AND PERMISSIONS (adjust as needed)
-- =====================================================

-- Grant usage on catalog (replace with your user/group)
-- GRANT USAGE ON CATALOG cfdb_dev TO `your-user@company.com`;
-- GRANT CREATE ON CATALOG cfdb_dev TO `your-user@company.com`;

-- Grant permissions on schemas
-- GRANT ALL PRIVILEGES ON SCHEMA cfdb_dev.bronze TO `your-user@company.com`;
-- GRANT ALL PRIVILEGES ON SCHEMA cfdb_dev.silver TO `your-user@company.com`;
-- GRANT ALL PRIVILEGES ON SCHEMA cfdb_dev.gold TO `your-user@company.com`;

-- =====================================================
-- VERIFY EXTERNAL LOCATION ACCESS
-- =====================================================

-- Test access to your S3 external location
-- Replace with your actual external location name if different
-- LIST 's3://ncaadata/';

-- Verify you can see the folder structure
-- LIST 's3://ncaadata/teams/';
-- LIST 's3://ncaadata/games/';
-- LIST 's3://ncaadata/plays/';

-- =====================================================
-- CATALOG INFORMATION QUERIES
-- =====================================================

-- Show all catalogs
SHOW CATALOGS;

-- Show schemas in cfdb_dev
SHOW SCHEMAS IN cfdb_dev;

-- Show current catalog context
SELECT current_catalog(), current_schema();