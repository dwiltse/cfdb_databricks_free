-- Databricks DLT Pipeline - Gold Layer Dimensional Model
-- File: teams_gold.sql

-- Current Team Dimension (Type 1 SCD)
CREATE OR REFRESH MATERIALIZED VIEW cfdb_dev.gold.dim_team (
  CONSTRAINT valid_team_id EXPECT (team_id IS NOT NULL),
  CONSTRAINT reasonable_data_year EXPECT (data_year >= YEAR(CURRENT_DATE()) - 2),
  CONSTRAINT has_conference EXPECT (conference_name IS NOT NULL),
  CONSTRAINT complete_team_info EXPECT (
    school_name IS NOT NULL 
    AND team_abbreviation IS NOT NULL 
    AND conference_name IS NOT NULL
  )
)
COMMENT "Gold layer - Current team dimension (Type 1 SCD) for operational analytics"
TBLPROPERTIES (
  "delta.autoOptimize.optimizeWrite" = "true",
  "delta.autoOptimize.autoCompact" = "true",
  "pipelines.autoOptimize.managed" = "true"
)
AS (
  WITH latest_teams AS (
    SELECT 
      *,
      ROW_NUMBER() OVER (
        PARTITION BY team_id 
        ORDER BY data_year DESC, silver_processed_at DESC NULLS LAST
      ) as row_number
    FROM cfdb_dev.silver.teams_cleaned
    WHERE team_id IS NOT NULL 
      AND school_name IS NOT NULL
      AND data_year >= YEAR(CURRENT_DATE()) - 5  -- Performance filter
  )
  SELECT 
    team_id,
    school_name,
    team_abbreviation,
    team_mascot,
    conference_name,
    division_name,
    venue_id,
    venue_name,
    venue_city,
    venue_state,
    venue_zip,
    venue_capacity,
    venue_construction_year,
    venue_latitude,
    venue_longitude,
    is_dome,
    has_grass_field,
    venue_elevation,
    venue_timezone,
    country_code,
    primary_logo_url,
    twitter_handle,
    data_year,
    venue_age,
    capacity_tier,
    geographic_region,
    data_completeness_score,
    CASE WHEN data_year = YEAR(CURRENT_DATE()) THEN true ELSE false END as is_current_season,
    YEAR(CURRENT_DATE()) - data_year as years_since_update,
    CONCAT(school_name, ' ', team_mascot) as team_display_name,
    CASE 
      WHEN division_name IS NOT NULL THEN CONCAT(conference_name, ' ', division_name)
      ELSE conference_name 
    END as conference_division_full,
    CURRENT_TIMESTAMP() as dim_last_updated
  FROM latest_teams
  WHERE row_number = 1
);

-- Historical Team Dimension (SCD Type 2) Target Table
CREATE OR REFRESH STREAMING TABLE cfdb_dev.gold.dim_team_scd (
  CONSTRAINT scd_valid_team_id EXPECT (team_id IS NOT NULL),
  CONSTRAINT scd_has_school EXPECT (school_name IS NOT NULL),
  CONSTRAINT scd_has_conference EXPECT (conference_name IS NOT NULL),
  CONSTRAINT scd_reasonable_year EXPECT (data_year >= 2000 AND data_year <= YEAR(CURRENT_DATE()) + 1)
)
COMMENT "Gold layer - Team historical dimension (Type 2 SCD) tracking conference realignment and changes over time"
TBLPROPERTIES (
  "delta.autoOptimize.optimizeWrite" = "true",
  "delta.autoOptimize.autoCompact" = "true",
  "pipelines.autoOptimize.managed" = "true"
);

-- APPLY CHANGES INTO for Automatic SCD Type 2
APPLY CHANGES INTO cfdb_dev.gold.dim_team_scd
FROM STREAM(cfdb_dev.silver.teams_cleaned)
KEYS (team_id)
SEQUENCE BY data_year
COLUMNS * EXCEPT (silver_processed_at)
STORED AS SCD TYPE 2;