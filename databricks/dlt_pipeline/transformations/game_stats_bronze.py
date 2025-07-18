# Databricks DLT Pipeline for Game Stats Data - Bronze Layer (Raw)
# File: game_stats_bronze.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# BRONZE LAYER - Raw game stats data ingestion (game_stats_bronze)
# =============================================================================

@dlt.table(
    name=f"{catalog}.bronze.game_stats_bronze",
    comment="Bronze layer - Raw game statistics data from CSV files with audit fields",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "bronze"
    }
)
@dlt.expect_or_fail("valid_game_id", "gameId IS NOT NULL")
@dlt.expect_or_drop("valid_team_id", "team IS NOT NULL")
def game_stats_bronze():
    """
    Ingests raw game statistics CSV data from S3 with audit fields.
    
    Source: s3://ncaadata/game_stats/
    """
    
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load("s3://ncaadata/game_stats/")
        
        # Add audit and tracking fields
        .withColumn("ingestion_timestamp", F.current_timestamp())
        .withColumn("source_file", F.col("_metadata.file_path"))
    )