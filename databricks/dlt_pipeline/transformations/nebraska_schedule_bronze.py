# Databricks DLT Pipeline for Nebraska 2025 Schedule - Bronze Layer
# File: nebraska_schedule_bronze.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# BRONZE LAYER - Nebraska 2025 schedule data
# =============================================================================

@dlt.table(
    name=f"{catalog}.bronze.nebraska_schedule_bronze",
    comment="Bronze layer - Nebraska 2025 schedule data from JSON file",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "bronze"
    }
)
@dlt.expect_or_fail("valid_season", "season IS NOT NULL AND season = 2025")
@dlt.expect_or_fail("valid_team", "team = 'Nebraska'")
def nebraska_schedule_bronze():
    """
    Ingests Nebraska 2025 schedule JSON data from S3 external location.
    
    Source: s3://ncaadata/2025_schedules/nebraska_2025_schedule.json
    
    The JSON file contains Nebraska's complete 2025 schedule with clean data.
    """
    
    # Define schema for Nebraska schedule JSON
    nebraska_schedule_schema = StructType([
        StructField("season", IntegerType(), True),
        StructField("team", StringType(), True),
        StructField("schedule", ArrayType(StructType([
            StructField("week", IntegerType(), True),
            StructField("date", StringType(), True),
            StructField("opponent", StringType(), True),
            StructField("home_away", StringType(), True),
            StructField("venue", StringType(), True),
            StructField("time", StringType(), True),
            StructField("neutral_site", BooleanType(), True)
        ])), True),
        StructField("summary", StructType([
            StructField("total_games", IntegerType(), True),
            StructField("home_games", IntegerType(), True),
            StructField("away_games", IntegerType(), True),
            StructField("neutral_site_games", IntegerType(), True)
        ]), True)
    ])
    
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "false")  # Use explicit schema
        .option("cloudFiles.schemaEvolutionMode", "rescue")
        .option("multiLine", "true")  # JSON files may span multiple lines
        .schema(nebraska_schedule_schema)
        .load("s3://ncaadata/2025_schedules/")
        
        # Add audit and tracking fields
        .withColumn("ingestion_timestamp", F.current_timestamp())
        .withColumn("source_file", F.col("_metadata.file_path"))
        .withColumn("file_modification_time", F.col("_metadata.file_modification_time"))
        
        # Add row-level identifier
        .withColumn("schedule_record_id", 
                   F.concat_ws("_", 
                              F.col("season").cast("string"),
                              F.col("team"),
                              F.regexp_extract(F.col("source_file"), r"([^/]+)\.json$", 1)
                   ))
    )

# =============================================================================
# BRONZE LAYER - Individual Nebraska games flattened
# =============================================================================

@dlt.table(
    name=f"{catalog}.bronze.nebraska_games_bronze",
    comment="Bronze layer - Individual Nebraska games flattened from schedule JSON",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "bronze"
    }
)
@dlt.expect_or_fail("valid_opponent", "opponent IS NOT NULL")
@dlt.expect_or_fail("valid_week", "week BETWEEN 1 AND 15")
def nebraska_games_bronze():
    """
    Flattens individual Nebraska games from the schedule JSON file.
    Each row represents a single scheduled game.
    """
    
    schedule_df = dlt.read_stream(f"{catalog}.bronze.nebraska_schedule_bronze")
    
    return (
        schedule_df
        .select(
            F.col("season"),
            F.col("team"),
            F.col("ingestion_timestamp"),
            F.col("source_file"),
            F.explode(F.col("schedule")).alias("game_data")
        )
        .select(
            "*",
            F.col("game_data.week").alias("week"),
            F.col("game_data.date").alias("game_date"),
            F.col("game_data.opponent").alias("opponent"),
            F.col("game_data.home_away").alias("home_away"),
            F.col("game_data.venue").alias("venue"),
            F.col("game_data.time").alias("game_time"),
            F.col("game_data.neutral_site").alias("neutral_site")
        )
        .drop("game_data")
        
        # Create standardized team fields for consistency with other tables
        .withColumn("home_team", 
                   F.when(F.col("home_away") == "home", F.col("team"))
                    .otherwise(F.col("opponent")))
        .withColumn("away_team",
                   F.when(F.col("home_away") == "away", F.col("team"))
                    .otherwise(F.col("opponent")))
        
        # Create unique game identifier
        .withColumn("nebraska_game_id",
                   F.concat_ws("_",
                              F.col("season").cast("string"),
                              F.col("week").cast("string"),
                              F.lit("nebraska"),
                              F.regexp_replace(F.lower(F.col("opponent")), r"[^a-zA-Z0-9]", "")
                   ))
        
        # Parse game datetime
        .withColumn("parsed_game_datetime",
                   F.when(F.col("game_date").isNotNull() & F.col("game_time").isNotNull(),
                          F.to_timestamp(F.concat_ws(" ", F.col("game_date"), F.col("game_time")), 
                                       "yyyy-MM-dd h:mm a")
                   ))
        
        # Add conference indicator (assume Big Ten opponents are conference games)
        .withColumn("is_conference_game",
                   F.when(F.col("opponent").isin([
                       "Michigan", "Michigan State", "Maryland", "Minneapolis", "Northwestern", 
                       "USC", "UCLA", "Penn State", "Iowa"
                   ]), True)
                    .otherwise(False))
    )