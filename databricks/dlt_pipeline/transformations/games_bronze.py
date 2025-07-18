# Databricks DLT Pipeline for Games Data - Bronze Layer (Raw)
# File: games_bronze.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# BRONZE LAYER - Raw games data ingestion (games_bronze)
# =============================================================================

@dlt.table(
    name=f"{catalog}.bronze.games_bronze",
    comment="Bronze layer - Raw games data from CSV files with audit fields",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "bronze"
    }
)
@dlt.expect_or_fail("valid_game_id", "id IS NOT NULL")
@dlt.expect_or_drop("valid_season", "season >= 2000 AND season <= 2030")
def games_bronze():
    """
    Ingests raw games CSV data from S3 with audit fields.
    
    Source: s3://ncaadata/games/
    """
    
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load("s3://ncaadata/games/")
        
        # Add audit and tracking fields
        .withColumn("ingestion_timestamp", F.current_timestamp())
        .withColumn("source_file", F.input_file_name())
    )