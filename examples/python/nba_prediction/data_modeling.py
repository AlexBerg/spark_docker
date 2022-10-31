from helper_functions import get_spark_session, read_from_csv, save_to_delta_table
from pyspark.sql import Window, SparkSession, DataFrame
from helper_functions import read_from_csv

import pyspark.sql.functions as F
import pyspark.sql.types as T

_path_to_raw = "examples/shared_datasets/"

def check_if_nba_tables_exist(spark: SparkSession) -> bool:
    table_names = ["Teams", "TeamSeasonStats", "Players", "PlayerSeasonAwardShare", "PlayerSeasonAdvancedStats",
        "PlayerSeasonPlayByPlayStats", "PlayerSeasonStats"]
    tables = spark.catalog.listTables()
    if any(all(table.name != table_name for table in tables) for table_name in table_names):
        return False
    
    return True


def drop_all_nba_tables(spark: SparkSession):
    table_names = ["Teams", "TeamSeasonStats", "Players", "PlayerSeasonAwardShare", "PlayerSeasonAdvancedStats",
        "PlayerSeasonPlayByPlayStats", "PlayerSeasonStats"]
    try:
        for table_name in table_names:
            spark.sql(f"DROP TALBE {table_name}")
    except Exception:
        print("Exception when trying to drop table.")


def create_nba_delta_tables(spark: SparkSession):
    teams = _create_team_tables(spark)

    _create_player_tables(spark, teams)


def _create_team_tables(spark: SparkSession) -> DataFrame:
    team_summaries = read_from_csv(spark, _path_to_raw + "Team Summaries.csv")\
        .filter("team != 'League Average'")
    
    abbrev = read_from_csv(spark, _path_to_raw + "Team Abbrev.csv")\
        .select("team", "lg", "season", "abbreviation")

    summaries_cond = [team_summaries.team == abbrev.team, team_summaries.season == abbrev.season, team_summaries.lg == abbrev.lg]
    team_summaries = team_summaries.join(abbrev, summaries_cond)\
        .drop(abbrev.season)\
        .drop(abbrev.lg)\
        .drop(abbrev.team)\
        .drop(team_summaries.abbreviation)

    teams = team_summaries.select(F.col("team").alias("TeamName"),
            F.col("abbreviation").alias("TeamNameShort"),
            F.col("lg").alias("League"))\
        .distinct()\
        .withColumn("TeamId", F.concat(F.hex(F.col("League")), F.hex(F.col("TeamNameShort"))))
    
    save_to_delta_table(teams, "Teams")

    season_stats_cond = [team_summaries.abbreviation == teams.TeamNameShort, team_summaries.lg == teams.League]
    team_season_stats = team_summaries.join(teams, season_stats_cond)\
        .select(F.col("TeamId"),
            F.col("TeamNameShort"),
            F.col("season").alias("Season"),
            F.col("playoffs").alias("MadePlayoffs").cast(T.BooleanType()),
            F.col("age").alias("AverageAge"),
            F.col("w").alias("Wins").cast(T.ShortType()),
            F.col("l").alias("Losses").cast(T.ShortType()),
            (F.col("w").cast(T.ShortType()) + F.col("l").cast(T.ShortType())).alias("GamesPlayed"),
            F.col("pw").alias("PredictedWins").cast(T.ShortType()),
            F.col("pl").alias("PredictedLosses").cast(T.ShortType()),
            F.col("mov").alias("AverageMarginOfVictory"),
            F.col("sos").alias("StrengthOfSchedule"),
            F.col("srs").alias("SimpleRating"),
            F.col("o_rtg").alias("OffensiveRating"),
            F.col("d_rtg").alias("DefensiveRating"),
            F.col("n_rtg").alias("NetRating"),
            F.col("pace").alias("Pace"),
            F.col("f_tr").alias("FreeThrowRate"),
            F.col("x3p_ar").alias("ThreePointAttemptRate"),
            F.col("ts_percent").alias("TrueShootingPercentage"),
            F.col("e_fg_percent").alias("EffectiveFieldGoalPercentage"),
            F.col("tov_percent").alias("TurnoverPercentage"),
            F.col("orb_percent").alias("OffensiveReboundPercentage"),
            F.col("ft_fga").alias("FreeThrowFactor"),
            F.col("opp_e_fg_percent").alias("OpponentEFGPercentage"),
            F.col("opp_tov_percent").alias("OpponentTOVPercentage"),
            F.col("opp_ft_fga").alias("OpponentFreeThrowFactor"))
    
    return_df = team_season_stats.select("TeamId", "TeamNameShort", "Season")

    team_season_stats = team_season_stats.drop("TeamNameShort")

    team_season_stats = _cast_column_to_float(team_season_stats)

    save_to_delta_table(team_season_stats, "TeamSeasonStats")

    return return_df

def _create_player_tables(spark: SparkSession, teams: DataFrame):
    
    _create_players_table(spark)

    _create_player_award_share_table(spark, teams)

    _create_player_season_advanced_stats_tables(spark, teams)

    _create_player_season_stats_table(spark, teams)

    _create_player_play_by_play_table(spark, teams)


def _create_players_table(spark: SparkSession):
    player_info = read_from_csv(spark, _path_to_raw + "Player Career Info.csv")\
        .select(F.col("player_id").alias("PlayerId"),
            F.col("player").alias("PlayerName"),
            F.col("hof").alias("MadeHallOfFame").cast(T.BooleanType()))

    save_to_delta_table(player_info, "Players")


def _create_player_award_share_table(spark: SparkSession, teams: DataFrame):
    player_award_share = read_from_csv(spark, _path_to_raw + "Player Award Shares.csv")

    player_award_share_cond = [player_award_share.tm == teams.TeamNameShort, player_award_share.season == teams.Season]

    player_award_share = player_award_share.join(teams, player_award_share_cond)\
        .select(F.col("award").alias("Award"),
            F.col("player_id").alias("PlayerId"),
            player_award_share.season.alias("Season"),
            F.col("TeamId"),
            F.col("pts_won").alias("PointsWon").cast(T.ShortType()),
            F.col("pts_max").alias("MaxPointsPossible").cast(T.ShortType()),
            F.col("share").alias("Share").cast(T.FloatType()),
            F.col("winner").alias("WonAward").cast(T.BooleanType()))

    save_to_delta_table(player_award_share, "PlayerSeasonAwardShare")


def _create_player_season_advanced_stats_tables(spark: SparkSession, teams: DataFrame):
    raise Exception("bro")


def _create_player_season_stats_table(spark: SparkSession, teams: DataFrame):
    raise Exception("bro")


def _create_player_play_by_play_table(spark: SparkSession, teams: DataFrame):
    raise Exception("bro")


def _cast_column_to_float(df: DataFrame) -> DataFrame:
    cols = [f.name for f in df.schema.fields if f.dataType == T.StringType()]

    for col in cols:
        if col != "Season" and col != "PlayerId" and col != "TeamId" and col != "Award":
            df = df.withColumn(col, F.col(col).cast(T.FloatType()))

    return df
