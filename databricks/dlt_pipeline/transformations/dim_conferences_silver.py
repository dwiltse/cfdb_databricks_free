# Databricks DLT Pipeline for Conferences Data - Silver Layer
# File: dim_conferences_silver.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# SILVER LAYER - Conference dimension with enhanced attributes
# =============================================================================

@dlt.table(
    name=f"{catalog}.silver_clean.conferences",
    comment="Silver layer - Conference dimension with classification and tier information",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "silver"
    }
)
@dlt.expect_or_fail("valid_conference_name", "conference_name IS NOT NULL")
@dlt.expect_or_fail("valid_division", "division_level IN ('FBS', 'FCS', 'Other')")
def conferences():
    """
    Conference dimension with tier classifications and competitive levels.
    """
    
    return (
        dlt.read(f"{catalog}.bronze_raw.conferences")
        .filter(F.col("name").isNotNull())
        .select(
            # Primary identifiers
            F.col("name").alias("conference_name"),
            F.col("abbreviation").alias("conference_abbrev"),
            F.col("division").alias("conference_division"),
            
            # Standardized division level
            F.when(F.col("division") == "fbs", F.lit("FBS"))
             .when(F.col("division") == "fcs", F.lit("FCS"))
             .otherwise(F.lit("Other")).alias("division_level"),
            
            # Conference tier classification
            F.when(F.col("name").isin(["SEC", "Big Ten", "Big 12", "ACC", "Pac-12"]), F.lit("Power 5"))
             .when(F.col("name").isin(["American Athletic", "Mountain West", "Conference USA", "Sun Belt", "Mid-American", "FBS Independents"]), F.lit("Group of 5"))
             .when(F.col("division") == "fbs", F.lit("Group of 5"))  # Catch any other FBS conferences
             .otherwise(F.lit("Non-FBS")).alias("conference_tier"),
            
            # Historical context
            F.when(F.col("name").isin(["SEC", "Big Ten", "ACC", "Pac-12", "Big 12"]), F.lit("Traditional Power"))
             .when(F.col("name").isin(["American Athletic", "Mountain West"]), F.lit("Modern Group of 5"))
             .when(F.col("name") == "FBS Independents", F.lit("Independent"))
             .otherwise(F.lit("Regional")).alias("conference_category"),
            
            # Competition level indicator
            F.when(F.col("name").isin(["SEC", "Big Ten", "Big 12", "ACC", "Pac-12"]), F.lit(1))
             .when(F.col("division") == "fbs", F.lit(2))
             .when(F.col("division") == "fcs", F.lit(3))
             .otherwise(F.lit(4)).alias("competition_level")
        )
    )