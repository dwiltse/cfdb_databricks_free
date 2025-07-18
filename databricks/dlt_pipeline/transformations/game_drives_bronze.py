# Databricks DLT Pipeline for Game Drives Data - Bronze Layer (Raw)
# File: game_drives_bronze.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# BRONZE LAYER - Raw game drives data ingestion (game_drives_bronze)
# =============================================================================

@dlt.table(
    name=f"{catalog}.bronze.game_drives_bronze",
    comment="Bronze layer - Raw game drives data from CSV files with audit fields",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "bronze"
    }
)
@dlt.expect_or_fail("valid_game_id", "gameId IS NOT NULL")
@dlt.expect_or_drop("valid_drive_id", "driveId IS NOT NULL")
def game_drives_bronze():
    """
    Ingests raw game drives CSV data from S3 with audit fields.
    
    Source: s3://ncaadata/game_drives/
    """
    
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load("s3://ncaadata/game_drives/")
        
        # Add audit and tracking fields
        .withColumn("ingestion_timestamp", F.current_timestamp())
        .withColumn("source_file", F.col("_metadata.file_path"))
    )