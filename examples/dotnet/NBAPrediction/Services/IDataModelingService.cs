using Microsoft.Spark.Sql;

namespace NBAPrediction.Services 
{
    internal interface IDataModelingService 
    {
        public void CreateNBADeltaTables(SparkSession spark);

        public void DropAllNBATables(SparkSession spark);
    }

}