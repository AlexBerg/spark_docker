from helper_functions import get_spark_session

from pyspark.ml import Pipeline
from pyspark.ml.stat import Correlation
from pyspark.ml.regression import RandomForestRegressionModel, RandomForestRegressor
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.sql import Window, SparkSession, DataFrame

import pyspark.sql.functions as F
import pyspark.sql.types as T


def _create_mvp_award_share_with_stats_dataset(spark: SparkSession) -> DataFrame:
    mvp_award_share_with_stats = spark.sql(
        """SELECT pt.* a.Share, a.Award, a.WonAward FROM (
                SELECT p.*, t.GamesPlayed as TeamGamesPlayed, t.League, ROUND(t.Wins / t.GamesPlayed, 2) AS WinPercentage, t.AverageMarginOfVictory, t.NetRating FROM
                (
                    SELECT past.*, pst.PointsPerGame, pst.AssistsPerGame, pst.StealsPerGame, pst.TotalReboundsPerGame, pst.BlocksPerGame, pst.GamesPlayed, pst.MinutesPerGame, pbp.OnCourtPlusMinusPer100Poss, pbp.NetPlusMinusPer100Poss, pbp.PointsGeneratedByAssistsPerGame FROM
                    PlayerSeasonStats AS pst
                    LEFT JOIN PlayerSeasonAdvancedStats AS past ON pst.PlayerId = past.PlayerId AND pst.Season = past.Season AND pst.TeamId = past.TeamId
                    LEFT JOIN PlayerSeasonPlayByPlay AS pbp ON pst.PlayerId = pbp.PlayerId AND pst.Season = pbp.Season AND pst.TeamId = pbp.TeamId
                ) AS p
                LEFT JOIN (
                    SELECT tst.*, team.League FROM
                    TeamSeasonStats AS tst
                    LEFT JOIN Teams AS team ON tst.TeamId = team.TeamId
                ) AS t
                ON p.TeamId = t.TeamId AND p.Season = t.Season
            ) as pt
            LEFT JOIN PlayerSeasonAwardShare AS a ON pt.PlayerId = a.PlayerId AND pt.Season = a.Season AND pt.TeamId = a.TeamId"""
        ).filter("""MinutesPerGame >= 20.0
            AND GamesStarted / GamesPlayed >= 0.50
            AND GamesPlayed / TeamGamesPlayed >= 0.50
            AND League = 'NBA'""")\
        .withColumn("Share", F.when(F.col("Award") == "nba mvp", F.col("Share")).otherwise(None))\
        .na.fill(0.0, ["Share"])\
        .na.fill(False, ["WonAward"])
    
    return mvp_award_share_with_stats   


if __name__ == "__main__":

    spark = get_spark_session()

    dataset = _create_mvp_award_share_with_stats_dataset(spark)       

    feature_columns = ["ValueOverReplacementPlayer", "PlayerEfficiencyRating", "WinShares", "TotalReboundPercentage", "AssistPercentage", "StealPercentage",
        "BlockPercentage", "TurnoverPercentage", "PointsPerGame", "OnCourtPlusMinusPer100Poss", "PointsGeneratedByAssitsPerGame", "NetPlusMinutPer100Poss", "AssistsPerGame",
        "StealsPerGame", "GamesStarted", "TotalReboundsPerGame", "BlocksPerGame", "WinPercentage"]

    train = dataset.filter("Season != 2022")
    test = dataset.filter("Season = 2022")

    assembler = VectorAssembler(inputCols=feature_columns, outputCol="features")
    train = assembler.transform(train)
    test = assembler.transform(test)

    rf = RandomForestRegressor(featuresCol="features", predictionCol="predicted_share", labelCol="Share", maxDepth=20, numTrees=60)

    pipeline = Pipeline(stages=[rf])

    mvp_model = pipeline.fit(train)

    predictions = mvp_model.transform(test)

    predictions = predictions.select("PlayerId", "Share", "predicted_share")\
        .withColumn("predicted_rank", F.when((F.col("predicted_share") < 0.05) & (F.col("share") == 0.0), 0)\
            .otherwise(F.row_number().over(Window.orderBy(F.desc("predicted_share"))).cast(T.FloatType())))\
        .withColumn("rank", F.when(F.col("share") == 0.0, 0).otherwise(F.row_number().over(Window.orderBy(F.desc("Share")))).cast(T.FloatType()))\
        .withColumn("rank_diff", F.abs(F.col("rank") - F.col("predicted_rank")))

    evaluator = RegressionEvaluator(predictionCol="predicted_share", labelCol="share", metricName="rmse")

    rmse = evaluator.evaluate(predictions)

    print(rmse)

