# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "84d4c516-90ee-4963-a892-2f1da3090e13",
# META       "default_lakehouse_name": "bronze",
# META       "default_lakehouse_workspace_id": "fde1670c-0b60-4fab-9a34-544986eb8788",
# META       "known_lakehouses": [
# META         {
# META           "id": "84d4c516-90ee-4963-a892-2f1da3090e13"
# META         }
# META       ]
# META     }
# META   }
# META }

# PARAMETERS CELL ********************

# Infer base parameters from the pipeline context
schemaName = ""
tableName = ""
filePath = ""

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Import functions
from pyspark.sql.functions import current_date

# Create schema
spark.sql(f'CREATE SCHEMA IF NOT EXISTS {schemaName}')

# Drop table
spark.sql(f'DROP TABLE IF EXISTS {schemaName}.{tableName}')

# Read data
df = spark.read.parquet(f"Files/{schemaName}/{filePath}/{tableName}.parquet")

# Add metadata loading_date column using current date
df = df.withColumn("loading_date", current_date().cast("string"))

# Overwrite table
df.write.mode("Overwrite").saveAsTable(f"{schemaName}.{tableName}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
