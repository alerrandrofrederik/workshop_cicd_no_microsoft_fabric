# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "bdf8983d-cdb5-4ff1-ae1f-655460db8890",
# META       "default_lakehouse_name": "gold",
# META       "default_lakehouse_workspace_id": "fde1670c-0b60-4fab-9a34-544986eb8788",
# META       "known_lakehouses": [
# META         {
# META           "id": "bdf8983d-cdb5-4ff1-ae1f-655460db8890"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql.functions import *

# Load data to the dataframe
dim_date = spark.read.table("silver.adventureworks.hist_salesorderheader") \
.where(col("current") == True)

dim_date = dim_date.dropDuplicates(["OrderDate"]).select(col("OrderDate"), \
        dayofmonth("OrderDate").alias("Day"), \
        month("OrderDate").alias("Month"), \
        year("OrderDate").alias("Year")
    ).orderBy("OrderDate")

# Add hash code using all selected columns
dim_date = dim_date.withColumn("ID", \
sha2(concat_ws("||", *dim_date.columns), 256))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from delta.tables import *

deltaTable = DeltaTable.forPath(spark, \
'Tables/adventureworks/dimension_date')

deltaTable.alias('gold') \
  .merge(
    dim_date.alias('updates'),
    'gold.ID = updates.ID'
  ).whenNotMatchedInsert(values =
    {
      "ID": "updates.ID",
      "OrderDate": "updates.OrderDate",
      "Day": "updates.Day",
      "Month": "updates.Month",
      "Year": "updates.Year",
    }
  ).execute()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
