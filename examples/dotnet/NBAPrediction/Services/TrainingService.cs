using Microsoft.Spark.Sql;
using Microsoft.ML;
using Microsoft.Data.Analysis;
using Microsoft.ML.Trainers;
using System.Collections.Generic;
using System;
using System.Linq;

using F = Microsoft.Spark.Sql.Functions;
using T = Microsoft.Spark.Sql.Types;
using D = Microsoft.ML.Data.DataKind;
using ML = Microsoft.ML;
using Spark = Microsoft.Spark;

namespace NBAPrediction.Services
{
    internal class TrainingService : ITrainingService
    {
        private readonly IHelperService _helperService;

        public TrainingService(IHelperService helperService)
        {
            _helperService = helperService;
        }

        public void TrainAndEvaluateMVPPredicitionModel(SparkSession spark)
        {
            try
            {
                var (mvpData, cols) = CreateMVPAwardShareWithStatsDataSet(spark);

                var seasonsWithData = mvpData.Select("Season").Distinct();

                var seasonToPredict = 1956; // First season nba mvp was awarded
                var latestSeason = 2022;

                var mlContext = new MLContext();
                var correctPredictions = new List<bool>();
                List<ML.Data.RegressionMetrics> allMetrics = new List<ML.Data.RegressionMetrics>();

                while (seasonToPredict <= latestSeason)
                {
                    if (seasonsWithData.Filter($"Season = {seasonToPredict}").Count() == 1)
                    {

                        SplitData(mvpData, seasonToPredict);
                        var model = TrainModel(mlContext, cols);

                        var (metrics, correctPrediction) = EvaluateModel(spark, mlContext, model, cols);

                        correctPredictions.Add(correctPrediction);
                        allMetrics.Add(metrics);
                    }

                    seasonToPredict += 1;
                }

                var accuratePredictions = correctPredictions.Count(x => x == true);
                var precentageCorrect = ((double)accuratePredictions / correctPredictions.Count()) * 100;
            }
            catch (System.Exception)
            {
                CleanupTempFiles();
                throw;
            }

            CleanupTempFiles();
        }

        private ITransformer TrainModel(MLContext mlContext, ML.Data.TextLoader.Column[] cols)
        {
            var trainingData = LoadFromCsvFile(mlContext, "datasets/temp/mvp/training/*.csv", cols);

            var pipeline = mlContext.Transforms
                .Concatenate("Features",
                    "ValueOverReplacementPlayer", "PlayerEfficiencyRating", "WinShares",
                    "TotalReboundPercentage", "AssistPercentage", "StealPercentage", "BlockPercentage", "TurnoverPercentage", "PointsPerGame", 
                    "OnCourtPlusMinusPer100Poss", "PointsGeneratedByAssitsPerGame", "NetPlusMinutPer100Poss", "AssistsPerGame", 
                    "StealsPerGame", "GamesStarted", "TotalReboundsPerGame", "BlocksPerGame", "WinPercentage")
                .Append(mlContext.Regression.Trainers.FastForest(labelColumnName: "Share", featureColumnName: "Features"));

            var model = pipeline.Fit(trainingData);

            return model;
        }

        private (ML.Data.RegressionMetrics metrics, bool predictedMVP) EvaluateModel(SparkSession spark, MLContext mlContext, ITransformer model, ML.Data.TextLoader.Column[] cols)
        {
            var testData = LoadFromCsvFile(mlContext, "datasets/temp/mvp/test/*.csv", cols);

            var predictions = model.Transform(testData);

            using (var stream = new System.IO.FileStream("datasets/temp/prediction.csv", System.IO.FileMode.Create))
            {
                mlContext.Data.SaveAsText(predictions, stream, ',', schema: false);
            }

            var df = _helperService.LoadFromCsv(spark, "/workspace/NBAPrediction/datasets/temp/prediction.csv")
                .Select("PlayerId", "Share", "Score")
                .WithColumn("Rank", F.When(F.Col("Share") == 0.0, 0)
                    .Otherwise(F.RowNumber().Over(Spark.Sql.Expressions.Window.OrderBy(F.Desc("Share")))).Cast("float"))
                .WithColumn("PredictedRank", F.When((F.Col("Score") < 0.05) & F.Col("Share") == 0.0, 0)
                    .Otherwise(F.RowNumber().Over(Spark.Sql.Expressions.Window.OrderBy(F.Desc("Score")))).Cast("float"))
                .WithColumn("Diff", F.Abs(F.Col("Rank") - F.Col("PredictedRank")))
                .Where("Rank != 0.0 AND PredictedRank != 0.0")
                .OrderBy(F.Col("Rank").Asc());

            var metrics = mlContext.Regression.Evaluate(predictions, "Share", "Score");

            if (df.Where("Rank = 1 AND PredictedRank = 1").Count() == 1)
                return (metrics, true);
            else
                return (metrics, false);
        }

        private IDataView LoadFromCsvFile(MLContext mlContext, string path, ML.Data.TextLoader.Column[] cols)
        {
            var dw = mlContext.Data.LoadFromTextFile(path, cols, separatorChar: ',', hasHeader: true);

            return dw;
        }

        private (Spark.Sql.DataFrame, ML.Data.TextLoader.Column[]) CreateMVPAwardShareWithStatsDataSet(SparkSession spark)
        {
            var mvpAwardShareWithStats = spark.Sql(
                    @"SELECT pt.*, a.Share, a.Award, a.WonAward FROM (
                        SELECT p.*, t.GamesPlayed AS TeamGamesPlayed, t.League, ROUND(t.Wins / t.GamesPlayed, 2) AS WinPercentage, t.AverageMarginOfVictory, t.NetRating FROM
                        (
                            SELECT past.*, pst.PointsPerGame, pst.AssistsPerGame, pst.StealsPerGame, pst.TotalReboundsPerGame, pst.BlocksPerGame, pst.GamesPlayed, pst.GamesStarted, pst.MinutesPerGame, pbp.OnCourtPlusMinusPer100Poss, pbp.NetPlusMinutPer100Poss, pbp.PointsGeneratedByAssitsPerGame FROM 
                            PlayerSeasonStats AS pst
                            LEFT JOIN PlayerSeasonAdvancedStats AS past ON pst.PlayerId = past.PlayerId AND pst.Season = past.Season AND pst.TeamId = past.TeamId
                            LEFT JOIN PlayerSeasonPlayByPlayStats AS pbp ON pst.PlayerId = pbp.PlayerId AND pst.Season = pbp.Season AND pst.TeamId = pbp.TeamId
                        ) AS p
                        LEFT JOIN (
                            SELECT tst.*, team.League FROM
                            TeamSeasonStats AS tst
                            LEFT JOIN Teams as team ON tst.TeamId = team.TeamId 
                        ) AS t
                        ON p.TeamId = t.TeamId AND p.Season = t.Season
                        ) as pt
                        LEFT JOIN PlayerSeasonAwardShare AS a ON pt.PlayerId = a.PlayerId AND pt.Season = a.Season AND pt.TeamId = a.TeamId"
            ).Filter(@"MinutesPerGame >= 20.0 
                AND GamesStarted / GamesPlayed >= 0.50 
                AND GamesPlayed / TeamGamesPlayed >= 0.50
                AND League = 'NBA'")
            .WithColumn("Share", F.When(F.Col("Award") == "nba mvp", F.Col("Share")).Otherwise(null))
            .Na().Fill(new Dictionary<string, double>() { { "Share", 0.0 } })
            .Na().Fill(new Dictionary<string, bool>() { { "WonAward", false } });

            var cols = GetColumns(mvpAwardShareWithStats);

            return (mvpAwardShareWithStats, cols);
        }

        private void SplitData(Spark.Sql.DataFrame mvpData, int season)
        {
            var trainingData = mvpData.Filter($"Season != {season}");
            var testData = mvpData.Filter($"Season = {season}");

            trainingData.Write().Format("csv").Option("header", true).Mode(SaveMode.Overwrite)
                .Save("/workspace/NBAPrediction/datasets/temp/mvp/training");

            testData.Write().Format("csv").Option("header", true).Mode(SaveMode.Overwrite)
                .Save("/workspace/NBAPrediction/datasets/temp/mvp/test");
        }

        private void CleanupTempFiles()
        {
            if (System.IO.Directory.Exists("datasets/temp"))
                System.IO.Directory.Delete("datasets/temp", true);
        }

        private ML.Data.TextLoader.Column[] GetColumns(Spark.Sql.DataFrame df)
        {
            var resultList = new List<ML.Data.TextLoader.Column>();
            var schema = df.Schema();
            var index = 0;
            foreach (var field in schema.Fields)
            {
                var fieldType = field.DataType.GetType();
                var type = fieldType == typeof(T.BooleanType) ? D.Boolean :
                    fieldType == typeof(T.StringType) ? D.String : D.Single;
                var col = new ML.Data.TextLoader.Column(field.Name, type, index);
                resultList.Add(col);
                index += 1;
            }

            return resultList.ToArray();
        }
    }
}