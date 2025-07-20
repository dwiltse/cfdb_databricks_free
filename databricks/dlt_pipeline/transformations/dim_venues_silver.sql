-- Databricks DLT Pipeline - Silver Layer
-- File: dim_venues_silver.sql

-- Venue dimension extracted from team locations
CREATE OR REFRESH MATERIALIZED VIEW LIVE.dim_venues_silver (
  CONSTRAINT valid_venue_id EXPECT (venue_id IS NOT NULL),
  CONSTRAINT valid_venue_name EXPECT (venue_name IS NOT NULL),
  CONSTRAINT valid_capacity EXPECT (venue_capacity IS NULL OR venue_capacity > 0)
)
COMMENT "Silver layer - Venue dimension with capacity tiers and geographic attributes"
TBLPROPERTIES (
  "delta.autoOptimize.optimizeWrite" = "true",
  "delta.autoOptimize.autoCompact" = "true",
  "pipelines.autoOptimize.managed" = "true"
)
AS (
  SELECT DISTINCT
    -- Primary identifiers
    location.id as venue_id,
    location.name as venue_name,
    
    -- Geographic information
    location.city as venue_city,
    location.state as venue_state,
    location.zip as venue_zip,
    location.countryCode as country_code,
    location.timezone as venue_timezone,
    
    -- Physical characteristics
    location.capacity as venue_capacity,
    location.constructionYear as year_built,
    location.dome as is_dome,
    location.grass as is_grass,
    location.elevation as venue_elevation,
    location.latitude,
    location.longitude,
    
    -- Calculated attributes
    YEAR(CURRENT_DATE()) - location.constructionYear as venue_age,
    
    CASE 
      WHEN location.capacity >= 80000 THEN 'Large (80K+)'
      WHEN location.capacity >= 60000 THEN 'Large (60K-80K)'
      WHEN location.capacity >= 40000 THEN 'Medium (40K-60K)'
      WHEN location.capacity >= 20000 THEN 'Small (20K-40K)'
      WHEN location.capacity IS NOT NULL THEN 'Small (<20K)'
      ELSE 'Unknown'
    END as capacity_tier,
    
    -- Regional classification
    CASE 
      WHEN location.state IN ('AL', 'AR', 'FL', 'GA', 'KY', 'LA', 'MS', 'NC', 'SC', 'TN', 'VA', 'WV') THEN 'Southeast'
      WHEN location.state IN ('TX', 'OK', 'KS', 'IA', 'MO', 'NE') THEN 'South Central'
      WHEN location.state IN ('OH', 'MI', 'IN', 'IL', 'WI', 'MN', 'ND', 'SD') THEN 'Midwest'
      WHEN location.state IN ('PA', 'NY', 'NJ', 'CT', 'MA', 'VT', 'NH', 'ME', 'RI', 'MD', 'DE') THEN 'Northeast'
      WHEN location.state IN ('CA', 'OR', 'WA', 'NV', 'AZ', 'UT', 'ID', 'MT', 'WY', 'CO', 'NM') THEN 'West'
      ELSE 'Other'
    END as geographic_region,
    
    -- Stadium era classification
    CASE 
      WHEN location.constructionYear >= 2000 THEN 'Modern (2000+)'
      WHEN location.constructionYear >= 1980 THEN 'Contemporary (1980-1999)'
      WHEN location.constructionYear >= 1960 THEN 'Classic (1960-1979)'
      WHEN location.constructionYear IS NOT NULL THEN 'Historic (Pre-1960)'
      ELSE 'Unknown Era'
    END as stadium_era,
    
    -- Playing surface type
    CASE 
      WHEN location.grass = true THEN 'Natural Grass'
      WHEN location.grass = false THEN 'Artificial Turf'
      ELSE 'Unknown Surface'
    END as surface_type,
    
    -- Climate control
    CASE 
      WHEN location.dome = true THEN 'Domed/Indoor'
      ELSE 'Outdoor'
    END as venue_type
    
  FROM LIVE.teams_bronze
  WHERE location.id IS NOT NULL 
    AND location.name IS NOT NULL
    AND classification = 'fbs' -- Only include FBS venues
);