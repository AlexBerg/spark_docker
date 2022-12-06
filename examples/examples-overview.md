# NBA prediction example projects
There are two example projects, one python and one dotnet, that aim to show how this docker setup can be used for local spark development and testing.
The example projects use dataset with [NBA stats from 1947 to present](https://www.kaggle.com/datasets/sumitrodatta/nba-aba-baa-stats?datasetId=1177523) found on [Kaggle](https://www.kaggle.com/) to train and evaluate models that try to predict the NBA mvp winner based on full season stats.

If you want to use iceberg instead of delta replace the following:

```
.config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")\
.config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")\
```
for 
```
.config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")\
.config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")\
```
in helper_functions.get_spark_session

and

```
df.writeTo(tableName).using("delta").create()
```

for

```
df.writeTo(tableName).using("iceberg").create()
```

in helper_functions.write_to_table