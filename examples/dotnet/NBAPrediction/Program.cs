using Microsoft.Spark.Sql;
using NBAPrediction.Services;


namespace NBAPrediction
{
    class Program
    {
        static void Main(string[] args)
        {
            var helper = new HelperService();
            var spark = helper.GetSparkSession();

            var training = new TrainingService(helper);
            var dataModeling = new DataModelingService(helper);

            if (!dataModeling.AllNBATablesExist(spark))
            {
                dataModeling.DropAllNBATables(spark);
                dataModeling.CreateNBADeltaTables(spark);
            }

            training.TrainAndEvaluateMVPPredictionModel(spark);
        }
    }
}