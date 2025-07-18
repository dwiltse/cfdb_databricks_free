# Databricks DLT Pipeline for Teams Data - Bronze Layer (Raw)
# File: teams_bronze.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# BRONZE LAYER - Raw teams data ingestion (teams_bronze)
# =============================================================================

@dlt.table(
    name=f"{catalog}.bronze.teams_bronze",
    comment="Bronze layer - Raw teams data from JSON files with audit fields",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "bronze"
    }
)
@dlt.expect_or_fail("valid_team_id", "id IS NOT NULL")
@dlt.expect_or_drop("valid_school_name", "school IS NOT NULL AND length(trim(school)) > 0")
def teams_bronze():
    """
    Ingests raw teams JSON data from S3 with audit fields.
    
    Source: s3://ncaadata/teams/
    """
    
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("multiline", "true")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load("s3://ncaadata/teams/")
        
        # Add audit and tracking fields
        .withColumn("ingestion_timestamp", F.current_timestamp())
        .withColumn("source_file", F.col("_metadata.file_path"))
    )