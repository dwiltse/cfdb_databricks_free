-- Databricks DLT Pipeline - Silver Layer
-- File: dim_conferences_silver.sql

-- Conference dimension with enhanced attributes
CREATE OR REFRESH MATERIALIZED VIEW LIVE.dim_conferences_silver (
  CONSTRAINT valid_conference_name EXPECT (conference_name IS NOT NULL),
  CONSTRAINT valid_division EXPECT (division_level IN ('FBS', 'FCS', 'Other'))
)
COMMENT "Silver layer - Conference dimension with classification and tier information"
TBLPROPERTIES (
  "delta.autoOptimize.optimizeWrite" = "true",
  "delta.autoOptimize.autoCompact" = "true",
  "pipelines.autoOptimize.managed" = "true"
)
AS (
  SELECT 
    -- Primary identifiers
    name as conference_name,
    abbreviation as conference_abbrev,
    division as conference_division,
    
    -- Standardized division level
    CASE 
      WHEN division = 'fbs' THEN 'FBS'
      WHEN division = 'fcs' THEN 'FCS' 
      ELSE 'Other'
    END as division_level,
    
    -- Conference tier classification
    CASE 
      WHEN name IN ('SEC', 'Big Ten', 'Big 12', 'ACC', 'Pac-12') THEN 'Power 5'
      WHEN name IN ('American Athletic', 'Mountain West', 'Conference USA', 'Sun Belt', 'Mid-American', 'FBS Independents') THEN 'Group of 5'
      WHEN division = 'fbs' THEN 'Group of 5' -- Catch any other FBS conferences
      ELSE 'Non-FBS'
    END as conference_tier,
    
    -- Historical context
    CASE 
      WHEN name IN ('SEC', 'Big Ten', 'ACC', 'Pac-12') THEN 'Traditional Power'
      WHEN name = 'Big 12' THEN 'Traditional Power'
      WHEN name IN ('American Athletic', 'Mountain West') THEN 'Modern Group of 5'
      WHEN name = 'FBS Independents' THEN 'Independent'
      ELSE 'Regional'
    END as conference_category,
    
    -- Competition level indicator
    CASE 
      WHEN name IN ('SEC', 'Big Ten', 'Big 12', 'ACC', 'Pac-12') THEN 1
      WHEN division = 'fbs' THEN 2
      WHEN division = 'fcs' THEN 3
      ELSE 4
    END as competition_level
    
  FROM LIVE.conferences_bronze
  WHERE name IS NOT NULL
);