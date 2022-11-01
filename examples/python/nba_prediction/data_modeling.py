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
            F.col("x3p_ar").alias("ThreePointerAttemptRate"),
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
    advanced_stats = read_from_csv(spark, _path_to_raw + "Advanced.csv").filter("tm != 'TOT'")

    advanced_stats_cond = [advanced_stats.tm == teams.TeamNameShort, advanced_stats.season == teams.Season]
    advanced_stats = advanced_stats.join(teams, advanced_stats_cond)\
        .select(F.col("player_id").alias("PlayerId"),
            advanced_stats.season.alias("Season"),
            F.col("TeamId"),
            F.col("per").alias("PlayerEfficiencyRating"),
            F.col("ts_percent").alias("TrueShootingPercentage"),
            F.col("x3p_ar").alias("ThreePointAttemptRate"),
            F.col("f_tr").alias("FreeThrowRate"),
            F.col("orb_percent").alias("OffensiveReboundPercentage"),
            F.col("drb_percent").alias("DefensiveReboundPercentage"),
            F.col("trb_percent").alias("TotalReboundPercentage"),
            F.col("ast_percent").alias("AssistPercentage"),
            F.col("stl_percent").alias("StealPercentage"),
            F.col("blk_percent").alias("BlockPercentage"),
            F.col("tov_percent").alias("TurnoverPercentage"),
            F.col("usg_percent").alias("UsagePercentage"),
            F.col("ows").alias("OffensiveWinShares"),
            F.col("dws").alias("DefensiveWinShares"),
            F.col("ws").alias("WinShares"),
            F.col("ws_48").alias("WinSharesPer48"),
            F.col("obpm").alias("OffensiveBoxPlusMinus"),
            F.col("dbmp").alias("DefensiveBoxPlusMinus"),
            F.col("bpm").alias("BoxPlusMinues"),
            F.col("vorp").alias("ValueOverReplacementPlayer"))\
        .na.replace("NA", None)

    advanced_stats = _cast_column_to_float(advanced_stats)

    save_to_delta_table(advanced_stats, "PlayerSeasonAdvancedStats")


def _create_player_season_stats_table(spark: SparkSession, teams: DataFrame):
    player_per_game_stats = read_from_csv(spark, _path_to_raw + "Player Per Game.csv").filter("tm != 'TOT'")

    player_per_game_stats_cond = [player_per_game_stats.tm == teams.TeamNameShort, player_per_game_stats.season == teams.Season]

    player_per_game_stats = player_per_game_stats.join(teams, player_per_game_stats_cond)\
        .select(F.col("player_id").alias("PlayerId"),
            player_per_game_stats.season.alias("Season"),
            F.col("TeamId"),
            F.col("g").alias("GamesPlayed").cast(T.ShortType()),
            F.col("gs").alias("GamesStarted").cast(T.ShortType()),
            F.col("mp_per_game").alias("MinutesPerGame"),
            F.col("pts_per_game").alias("PointsPerGame"),
            F.col("fg_per_game").alias("FieldGoalsPerGame"),
            F.col("fga_per_game").alias("FieldGoalsAttemptedPerGame"),
            F.col("fg_percent").alias("FieldGoalPercentage"),
            F.col("x3p_per_game").alias("ThreePointersPerGame"),
            F.col("x3pa_per_game").alias("ThreePointersAttemptedPerGame"),
            F.col("x3p_percent").alias("ThreePointerPercentage"),
            F.col("x2p_per_game").alias("TwoPointersPerGame"),
            F.col("x2pa_per_game").alias("TwoPointersAttemptedPerGame"),
            F.col("x2p_percent").alias("TwoPointerPercentage"),
            F.col("e_fg_percent").alias("EffectiveFieldGoalPercentage"),
            F.col("ft_per_game").alias("FreeThrowsPerGame"),
            F.col("fta_per_game").alias("FreeThrowsAttemptedPerGame"),
            F.col("ft_percent").alias("FreeThrowPercentage"),
            F.col("orb_per_game").alias("OffensiveReboundsPerGame"),
            F.col("drb_per_game").alias("DefensiveReboundsPerGame"),
            F.col("trb_per_game").alias("TotalReboundsPerGame"),
            F.col("ast_per_game").alias("AssistsPerGame"),
            F.col("stl_per_game").alias("StealsPerGame"),
            F.col("blk_per_game").alias("BlocksPerGame"),
            F.col("tov_per_game").alias("TurnoversPerGame"),
            F.col("pf_per_game").alias("PersonalFoulsPerGame"))\
        .na.replace("NA", None)

    player_per_game_stats = _cast_column_to_float(player_per_game_stats)

    save_to_delta_table(player_per_game_stats, "PlayerSeasonStats")



def _create_player_play_by_play_table(spark: SparkSession, teams: DataFrame):
    play_by_play = read_from_csv(spark, _path_to_raw + "Player Play by Play.csv").filter("tm != 'TOT'")

    play_by_play_cond = [play_by_play.tm == teams.TeamNameShort, play_by_play.season == teams.Season]

    play_by_play = play_by_play.join(teams, play_by_play_cond)\
        .select(F.col("player_id").alias("PlayerId"),
            play_by_play.season.alias("Season"),
            F.col("TeamId"),
            F.col("pg_percent").alias("PointGuardPercent"),
            F.col("sg_percent").alias("ShootingGuardPercent"),
            F.col("sf_percent").alias("SmallForwardPercent"),
            F.col("pf_percent").alias("PowerForwardPercent"),
            F.col("c_percent").alias("CenterPercentage"),
            F.col("on_court_plus_minus_per_100_poss").alias("OnCourtPlusMinusPer100Poss"),
            F.col("net_plus_minus_per_100_poss").alias("NetPlusMinusPer100Poss"),
            F.round(F.col("shooting_foul_drawn") / F.col("g"), 2).alias("ShootingFoulDrawnPerGame"),
            F.round(F.col("offensive_foul_drawn") / F.col("g"), 2).alias("OffensiveFoulDrawnPerGame"),
            F.round(F.col("points_generated_by_assists") / F.col("g"), 2).alias("PointsGeneratedByAssistsPerGame"),
            F.round(F.col("and1") / F.col("g"), 2).alias("And1PerGame"))\
        .na.replace("NA", None)

    play_by_play = _cast_column_to_float(play_by_play)

    save_to_delta_table(play_by_play, "PlayerSeasonPlayByPlayStats")


def _cast_column_to_float(df: DataFrame) -> DataFrame:
    cols = [f.name for f in df.schema.fields if f.dataType == T.StringType()]

    for col in cols:
        if col != "Season" and col != "PlayerId" and col != "TeamId" and col != "Award":
            df = df.withColumn(col, F.col(col).cast(T.FloatType()))

    return df
