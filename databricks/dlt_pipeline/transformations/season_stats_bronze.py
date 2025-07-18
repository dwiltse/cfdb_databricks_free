# Databricks DLT Pipeline for Season Stats Data - Bronze Layer (Raw)
# File: season_stats_bronze.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# BRONZE LAYER - Raw season stats data ingestion (season_stats_bronze)
# =============================================================================

@dlt.table(
    name=f"{catalog}.bronze.season_stats_bronze",
    comment="Bronze layer - Raw season statistics data from CSV files with audit fields",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "bronze"
    }
)
@dlt.expect_or_fail("valid_season", "season IS NOT NULL")
@dlt.expect_or_drop("valid_team_id", "team IS NOT NULL")
def season_stats_bronze():
    """
    Ingests raw season statistics CSV data from S3 with audit fields.
    
    Source: s3://ncaadata/season_stats/
    """
    
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load("s3://ncaadata/season_stats/")
        
        # Add audit and tracking fields
        .withColumn("ingestion_timestamp", F.current_timestamp())
        .withColumn("source_file", F.col("_metadata.file_path"))
    )