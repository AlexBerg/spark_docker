from helper_functions import get_spark_session, read_from_delta
from data_cleaning_shared import get_player_per_game_stats

from pyspark.ml import Pipeline
from pyspark.ml.stat import Correlation
from pyspark.ml.regression import RandomForestRegressionModel, RandomForestRegressor
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.sql import Window

import pyspark.sql.functions as F
import pyspark.sql.types as T

if __name__ == "__main__":

    spark = get_spark_session()

    per_game_stats = get_player_per_game_stats(spark)

    per_game_stats = per_game_stats.na.drop()

    mvps = read_from_delta(spark, "delta/mvp_with_stats")\
        .select(F.col("player_id").alias("player_id_mvp"), 
            F.col("season").alias("season_mvp"), "share")

    conditions = [
        per_game_stats.player_id == mvps.player_id_mvp,
        per_game_stats.season == mvps.season_mvp
    ]

    dataset = per_game_stats.join(mvps, conditions, "left")\
        .drop("season_mvp", "player_id_mvp")\
        .fillna({"share": 0.0})\
        .filter("season != 2022")

    feature_columns = ["g", "gs", "pts_per_game", "per", "ast_percent", "stl_percent", "blk_percent", "ts_percent", "trb_per_game", "ast_per_game",
        "stl_per_game", "blk_per_game", "tov_per_game", "dws", "ows", "bpm", "vorp"]

    train = dataset.filter("season != 2021")
    test = dataset.filter("season = 2021")

    assembler = VectorAssembler(inputCols=feature_columns, outputCol="predictors")
    train = assembler.transform(train)
    test = assembler.transform(test)

    rf = RandomForestRegressor(featuresCol="predictors", predictionCol="predicted_share", labelCol="share", maxDepth=20, numTrees=60)

    pipeline = Pipeline(stages=[rf])

    mvp_model = pipeline.fit(train)

    predictions = mvp_model.transform(test)

    predictions = predictions.select("player_id", "player", "share", "predicted_share")\
        .withColumn("predicted_rank", F.when((F.col("predicted_share") < 0.05) & (F.col("share") == 0.0), 0)\
            .otherwise(F.row_number().over(Window.orderBy(F.desc("predicted_share"))).cast(T.FloatType())))\
        .withColumn("rank", F.when(F.col("share") == 0.0, 0).otherwise(F.row_number().over(Window.orderBy(F.desc("share")))).cast(T.FloatType()))\
        .withColumn("rank_diff", F.abs(F.col("rank") - F.col("predicted_rank")))

    evaluator = RegressionEvaluator(predictionCol="predicted_share", labelCol="share", metricName="rmse")

    rmse = evaluator.evaluate(predictions)

    print(rmse)

