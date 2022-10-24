Use the commands below to build and run the example as outline at https://github.com/dotnet/spark/blob/master/docs/getting-started/ubuntu-instructions.md

dotnet build

cp people.json /dotnet/HelloSpark/bin/Debug/netcoreapp3.1
cd /dotnet/HelloSpark/bin/Debug/netcoreapp3.1

####### spark-3.2.1 #######
# Run locally
spark-submit --class org.apache.spark.deploy.dotnet.DotnetRunner --master local microsoft-spark-3-2_2.12-2.1.1.jar dotnet HelloSpark.dll

# To test out the example using the master and slave instances
spark-submit --class org.apache.spark.deploy.dotnet.DotnetRunner --master spark://$HOSTNAME:$SPARK_MASTER_PORT microsoft-spark-3-2_2.12-2.1.1.jar dotnet HelloSpark.dll