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

# Load data to the dataframe as a starting point to create the gold layer
customer = spark.read.table("silver.adventureworks.hist_customer") \
.where(col("current") == True)
customer = customer.dropDuplicates(["CustomerID"])
dimension_customer = customer[["CustomerID", "Title", "FirstName", \
"MiddleName", "LastName", "CompanyName", "EmailAddress", "Phone"]]

# Add hash code using all selected columns
dimension_customer = dimension_customer.withColumn("ID", \
sha2(concat_ws("||", *dimension_customer.columns), 256))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from delta.tables import *

deltaTable = DeltaTable.forPath(spark, \
'Tables/adventureworks/dimension_customer')

deltaTable.alias('gold') \
  .merge(
    dimension_customer.alias('updates'),
    'gold.ID = updates.ID'
  ).whenMatchedUpdate(set =
    {
      "current_flag": lit("1"),
      "current_date": current_date(),
      "end_date": """to_date('9999-12-31', 'yyyy-MM-dd')"""
    }
  ).whenNotMatchedInsert(values =
    {
      "ID": "updates.ID",
      "CustomerID": "updates.CustomerID",
      "Title": "updates.Title",
      "FirstName": "updates.FirstName",
      "MiddleName": "updates.MiddleName",
      "LastName": "updates.LastName",
      "CompanyName": "updates.CompanyName",
      "EmailAddress": "updates.EmailAddress",
      "Phone": "updates.Phone",
      "current_flag": lit("1"),
      "current_date": current_date(),
      "end_date": """to_date('9999-12-31', 'yyyy-MM-dd')"""
    }
  ).whenNotMatchedBySourceUpdate(set =
    {
      "current_flag": lit("0"),
      "end_date": current_date()
    }
  ).execute()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
