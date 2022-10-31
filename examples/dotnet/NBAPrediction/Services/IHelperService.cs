using Microsoft.Spark.Sql;
using System.Collections.Generic;

namespace NBAPrediction.Services
{
    internal interface IHelperService
    {
        public SparkSession GetSparkSession();
        public DataFrame LoadFromCsv(SparkSession spark, string path);
        public void CreateOrOverwriteManagedDeltaTable(DataFrame dataFrame, string tableName);
        public DataFrame LoadFromManagedDeltaTable(SparkSession spark, string tableName);
    }
}
