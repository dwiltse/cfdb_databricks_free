# Databricks DLT Pipeline for Plays Data - Bronze Layer (Raw)
# File: plays_bronze.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# BRONZE LAYER - Raw plays data ingestion (plays_bronze)
# =============================================================================

@dlt.table(
    name=f"{catalog}.bronze.plays_bronze",
    comment="Bronze layer - Raw play-by-play data from Parquet files, partitioned by year, with audit fields",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "bronze"
    }
)
@dlt.expect_or_fail("valid_game_id", "gameId IS NOT NULL")
@dlt.expect_or_drop("valid_drive_id", "driveId IS NOT NULL")
def plays_bronze():
    """
    Ingests raw play-by-play Parquet data from S3 with audit fields.
    Data is partitioned by year in nested folders.
    
    Source: s3://ncaadata/plays/ (with year subfolders like 2024/)
    """
    
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "parquet")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .option("recursiveFileLookup", "true")  # Important for nested year folders
        .load("s3://ncaadata/plays/")
        
        # Add audit and tracking fields
        .withColumn("ingestion_timestamp", F.current_timestamp())
        .withColumn("source_file", F.input_file_name())
        # Extract year from file path for partitioning
        .withColumn("year_partition", F.regexp_extract(F.input_file_name(), r"plays/(\d{4})/", 1).cast("integer"))
    )