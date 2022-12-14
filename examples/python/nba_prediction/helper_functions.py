from pyspark.sql import SparkSession, DataFrame

def get_spark_session() -> SparkSession:
    return  SparkSession.builder.appName("nba_predicition")\
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")\
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")\
        .enableHiveSupport()\
        .getOrCreate()

def read_from_csv(spark: SparkSession, path: str) -> DataFrame:
    return spark.read.format("csv")\
            .option("inferSchema", True)\
            .option("header", True)\
            .option("sep", ",")\
            .load(path)

def write_to_table(df: DataFrame, tableName: str):
    df.writeTo(tableName).using("delta").create()

def read_from_table(spark: SparkSession, tableName: str):
    return spark.read.table(tableName)