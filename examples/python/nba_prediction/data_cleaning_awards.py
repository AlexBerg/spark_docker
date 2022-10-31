from pyspark.sql import Window
from helper_functions import get_spark_session, read_from_csv, save_to_delta_table
from data_cleaning_shared import get_player_per_game_stats

import pyspark.sql.functions as F
import pyspark.sql.types as T

spark = get_spark_session()

award_winners = read_from_csv(spark, "nba_prediction/datasets/Player Award Shares.csv")\
    .select("season", "player_id", "share", "award")\
    .withColumnRenamed("season", "season_award")\
    .withColumnRenamed("player_id", "player_id_award")

player_per_game_stats = get_player_per_game_stats(spark)

award_conditions = [
    player_per_game_stats.player_id == award_winners.player_id_award,
    player_per_game_stats.season == award_winners.season_award
]    

award_winners_with_stats = player_per_game_stats.join(award_winners, award_conditions, "inner").drop("player_id_award", "season_award")\
    .withColumn("share", F.col("share").cast(T.FloatType()))
mvps_with_stats = award_winners_with_stats.filter("award = 'nba mvp'").drop("award")
dpoys_with_stats = award_winners_with_stats.filter("award = 'dpoy'").drop("award")

save_to_delta_table(mvps_with_stats, "MvpsWithStats")
save_to_delta_table(dpoys_with_stats, "DpoysWithStats")