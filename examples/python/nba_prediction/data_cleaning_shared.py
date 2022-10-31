from pyspark.sql import Window, SparkSession, DataFrame
from helper_functions import read_from_csv

import pyspark.sql.functions as F
import pyspark.sql.types as T

def get_player_per_game_stats(spark: SparkSession) -> DataFrame:
    player_per_game_stats = read_from_csv(spark, "nba_prediction/datasets/Player Per Game.csv")
    player_advanced_stats = read_from_csv(spark, "nba_prediction/datasets/Advanced.csv")\
        .select("season", "player_id", "per", "ts_percent", "trb_percent", "ast_percent", "stl_percent", "blk_percent",
        "tov_percent", "usg_percent", "ows", "dws", "ws", "ws_48", "obpm", "dbpm", "bpm", "vorp")\
        .withColumnRenamed("season", "season_adv")\
        .withColumnRenamed("player_id", "player_id_adv")
    team_summaries = read_from_csv(spark, "nba_prediction/datasets/Team summaries.csv")\
        .filter("lg = 'NBA'")\
        .withColumn("tg", F.col("w") + F.col("l"))\
        .withColumn("t_w_percent", F.col("w") / F.col("tg"))\
        .select(F.col("season").alias("tm_season"), "abbreviation", "tg", "t_w_percent")

    w = Window.partitionBy("season", "player_id", "player")

    conditions_1 = [
        player_per_game_stats.season == team_summaries.tm_season,
        player_per_game_stats.tm == team_summaries.abbreviation
    ]

    conditions_2 = [
        player_per_game_stats.player_id == player_advanced_stats.player_id_adv,
        player_per_game_stats.season == player_advanced_stats.season_adv
    ]

    player_per_game_stats = player_per_game_stats.filter("lg = 'NBA' AND tm != 'TOT'").withColumn("num_team", F.count("player").over(w))\
        .filter("num_team = 1 AND gs > 0.0 AND gs / g >= 0.50")\
        .join(team_summaries, conditions_1, "left")\
        .filter("tg IS NULL or g / tg >= 0.50")\
        .select("season", "player_id", "player", "tm", "t_w_percent", "g", "gs", "mp_per_game", "fga_per_game", "fg_percent", "e_fg_percent", "trb_per_game",
            "ast_per_game", "stl_per_game", "blk_per_game", "tov_per_game", "pts_per_game")\
        .join(player_advanced_stats, conditions_2, "left")\
        .replace('NA', None)\
        .drop("player_id_adv", "season_adv")

    for col in player_per_game_stats.columns:
        if col != "player" and col != "tm" and col != "player_id" and col != "season":
            player_per_game_stats = player_per_game_stats.withColumn(col, F.col(col).cast(T.FloatType()))

    return player_per_game_stats