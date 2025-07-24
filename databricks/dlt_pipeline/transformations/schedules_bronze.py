# Databricks DLT Pipeline for Schedule Data - Bronze Layer (Raw)
# File: schedules_bronze.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# BRONZE LAYER - Raw schedule data ingestion (schedules_bronze)
# =============================================================================

@dlt.table(
    name=f"{catalog}.bronze.schedules_bronze",
    comment="Bronze layer - Raw 2025 schedule data from scraped JSON files",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "bronze"
    }
)
@dlt.expect_or_fail("valid_season", "season IS NOT NULL AND season = 2025")
def schedules_bronze():
    """
    Ingests raw 2025 schedule JSON data from S3 external location.
    
    Source: s3://ncaadata/2025_schedules/
    
    The JSON files contain nested game data that needs to be flattened:
    - Master schedule files with metadata
    - Weekly schedule files with game details
    """
    
    # Define schema for the JSON data based on your scraped files
    schedule_schema = StructType([
        StructField("season", IntegerType(), True),
        StructField("scraped_timestamp", StringType(), True),
        StructField("source", StringType(), True),
        StructField("metadata", StructType([
            StructField("total_weeks", IntegerType(), True),
            StructField("extraction_method", StringType(), True),
            StructField("data_quality", StringType(), True),
            StructField("includes_betting_lines", BooleanType(), True),
            StructField("includes_venues", BooleanType(), True),
            StructField("includes_tv_networks", BooleanType(), True),
            StructField("includes_game_times", BooleanType(), True)
        ]), True),
        StructField("key_findings", MapType(StringType(), StructType([
            StructField("week", IntegerType(), True),
            StructField("date", StringType(), True),
            StructField("time", StringType(), True),
            StructField("away_team", StringType(), True),
            StructField("home_team", StringType(), True),
            StructField("venue", StringType(), True),
            StructField("tv_network", StringType(), True),
            StructField("betting_lines", StringType(), True),
            StructField("neutral_site", BooleanType(), True),
            StructField("away_score", IntegerType(), True),
            StructField("home_score", IntegerType(), True),
            StructField("game_status", StringType(), True),
            StructField("note", StringType(), True)
        ])), True)
    ])
    
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "false")  # Use explicit schema
        .option("cloudFiles.schemaEvolutionMode", "rescue")
        .option("multiLine", "true")  # JSON files may span multiple lines
        .schema(schedule_schema)
        .load("s3://ncaadata/2025_schedules/")
        
        # Add audit and tracking fields
        .withColumn("ingestion_timestamp", F.current_timestamp())
        .withColumn("source_file", F.col("_metadata.file_path"))
        .withColumn("file_modification_time", F.col("_metadata.file_modification_time"))
        
        # Add row-level identifier for deduplication
        .withColumn("schedule_record_id", 
                   F.concat_ws("_", 
                              F.col("season").cast("string"),
                              F.col("source"),
                              F.regexp_extract(F.col("source_file"), r"([^/]+)\.json$", 1)
                   ))
    )

# =============================================================================
# BRONZE LAYER - Flattened games from schedule data
# =============================================================================

@dlt.table(
    name=f"{catalog}.bronze.schedule_games_bronze",
    comment="Bronze layer - Individual games extracted from schedule JSON files",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "bronze"
    }
)
@dlt.expect_or_fail("valid_teams", "away_team IS NOT NULL AND home_team IS NOT NULL")
def schedule_games_bronze():
    """
    Flattens individual games from the schedule JSON files.
    Each row represents a single scheduled game with all metadata.
    """
    
    schedule_df = dlt.read_stream(f"{catalog}.bronze.schedules_bronze")
    
    return (
        schedule_df
        .select(
            F.col("season"),
            F.col("source"),
            F.col("ingestion_timestamp"),
            F.col("source_file"),
            F.explode(F.col("key_findings")).alias("game_key", "game_data")
        )
        .select(
            "*",
            F.col("game_data.week").alias("week"),
            F.col("game_data.date").alias("game_date"),
            F.col("game_data.time").alias("game_time"),
            F.col("game_data.away_team").alias("away_team"),
            F.col("game_data.home_team").alias("home_team"),
            F.col("game_data.venue").alias("venue"),
            F.col("game_data.tv_network").alias("tv_network"),
            F.col("game_data.betting_lines").alias("betting_lines"),
            F.col("game_data.neutral_site").alias("neutral_site"),
            F.col("game_data.away_score").alias("away_score"),
            F.col("game_data.home_score").alias("home_score"),
            F.col("game_data.game_status").alias("game_status"),
            F.col("game_data.note").alias("game_note"),
            F.col("game_key").alias("game_identifier")
        )
        .drop("game_data", "game_key")
        .filter(F.col("week").isNotNull())  # Only include records that have week data
        
        # Create unique game identifier
        .withColumn("schedule_game_id",
                   F.concat_ws("_",
                              F.col("season").cast("string"),
                              F.col("week").cast("string"),
                              F.regexp_replace(F.col("away_team"), r"[^a-zA-Z0-9]", ""),
                              F.regexp_replace(F.col("home_team"), r"[^a-zA-Z0-9]", "")
                   ))
        
        # Parse datetime if possible
        .withColumn("parsed_game_datetime",
                   F.when(F.col("game_date").isNotNull() & F.col("game_time").isNotNull(),
                          F.to_timestamp(F.concat_ws(" ", F.col("game_date"), F.col("game_time")), 
                                       "yyyy-MM-dd h:mm a")
                   ))
    )