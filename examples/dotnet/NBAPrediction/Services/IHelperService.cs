using Microsoft.Spark.Sql;
using System.Collections.Generic;

namespace NBAPrediction.Services
{
    internal interface IHelperService
    {
        public SparkSession GetSparkSession();
        public DataFrame ReadFromCsv(SparkSession spark, string path);
        public void WriteToDeltaTable(DataFrame dataFrame, string tableName);
        public DataFrame ReadFromDeltaTable(SparkSession spark, string tableName);
    }
}
