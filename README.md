**_IMPORTANT:_** There are <b>dummy passwords</b> in the shared/templates/hive-site.xml, shared/templates/sql-scripts/init_metastore.sql, shared/templats/sql-scripts/entrypoint.sh and docker-compose.spark-dotnet.yml files that you <b>should absolutely change before running this</b>.

# Spark docker setup
## Introduction
The purpose for this project is to provide a easy to use dockerized spark environment setup that resembels something you would find out in the "real" world to use for local development.
The general setup is one container for spark, one for hive and one for sql server. This reflects a spark setup with a external hive metastore using sql server as the
database for the metastore.

There are currently two different configurations available: spark with conda to be used for pyspark based development or a .NET spark configuration for development
in .NET. Both setups include support for Delta Lake.

### Versions used
* Spark 3.2.1
* Hive 2.3.9
* SQL Server 2019(latest)
* .NET Core 3.1
* .NET Spark 2.1.1
* Conda latest linux version
* Delta lake 1.2.1

## Spark with conda container
This container comes with latest linux version of conda pre-installed and initalized in the bash shell.

## .NET spark container
This container comes with .NET Core 3.1 and used .NET Spark 2.1.1, which means the corresponding nuget package to add to utilize .NET Spark is 
Microsoft.Spark version 2.1.1


## How to use
1. Run the build.sh file found in the docker folder with either -c\--conda or -d\--dotnet flags to build the images for either python based development or
   .NET based development respectivly.
2. Run docker compose -f docker-compose.spark-conda.yml\docker-compose.spark-dotnet.yml up -d in the docker folder to create\update and start the containers for
   the resoective environment.
3. Start VSCode and attach to the running spark container
4. Open the workspace folder in the container in VSCode
5. Proceed as normal when developing in either python or .NET! (Important to note that this only tested with .NET Core 3.1 for now)



Originally inspired by and adopted from the [3rdman dotnet-spark project](https://github.com/indy-3rdman/docker-dotnet-spark)
