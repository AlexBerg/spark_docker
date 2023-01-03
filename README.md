**_IMPORTANT:_** Change the dummy passwords in the compose files to replace dummy passwords scattered through different configuration files and scripts.</b>.

# Spark docker setup
## Introduction
The purpose for this project is to provide a easy to use dockerized spark environment setup that resembels something you would find out in the "real" world to use for local development.
The general setup is one container for spark, one for hive and one for sql server. This reflects a spark setup with a external hive metastore using sql server as the
database for the metastore.

There are currently two different configurations available: spark with conda to be used for pyspark based development or a .NET spark configuration for development
in .NET. Both setups include support for Delta Lake.

### Versions used
The reason for the different setups using different spark version is simply that the highest version of Spark currently supported by Spark DotNet is 3.2.1

#### Shared
* Hive metastore 3.1.2 (Hadoop 3.3.2)
* Postgres 15.1
* Minio latest version (Dockerfile will pull latest minio image)
* Apache Superset 1.5.2
#### Python (Conda)
* Spark 3.3.1 (Hadoop 3.3.2)
* Delta lake 2.1.1
* Conda (Dockerfile downloads and installs latest conda version)
#### Dotnet
* Spark 3.2.1 (Hadoop 3.3.1) 
* .NET Core 3.1
* .NET Spark 2.1.1
* Delta lake 2.0.1
#### GPU
* CUDA 11.4.0 (Can be changed to a different version in the build.sh file)

**_NOTE:_** When installing Spark 3.2.1 with Hadoop 3.x pre compiled the file name in the archive says hadoop3.2. The actual spark installation actually comes with
Hadoop 3.3.1 pre-compiled, and not 3.2.x. 

## Spark with conda container
This container comes with latest linux version of conda pre-installed and initalized in the bash shell.

## .NET spark container
This container comes with .NET Core 3.1 and used .NET Spark 2.1.1, which means the corresponding nuget package to add to utilize .NET Spark is 
Microsoft.Spark version 2.1.1


## How to use
1. Run the build.sh file found in the docker folder with either -c\--conda or -d\--dotnet flags to build the images for either python based development or
   .NET based development respectivly.
2. Run either <b>docker compose -f docker-compose.shared.yml -f docker-compose.spark-conda.yml up --build -d</b> or <b>docker compose -f docker-compose.shared.yml -f docker-compose.spark-dotnet.yml up --build -d</b> in the docker folder to create\update and start the containers for the respective environment. The --build flag is to makes sure it rebuilds the images to use the passwords passed as arguments from the compose file.
3. Start VSCode and attach to the running spark container
4. Open the workspace folder in the container in VSCode
5. Proceed as normal when developing in either python or .NET! (Important to note that this only tested with .NET Core 3.1 for now). There are example projects in the example folder that exemplify this.

### Use GPU
To enable GPU support in the docker container there are two things that are required:
1. Add the -g\--gpu flag when running the build.sh file.
2. Change the spark container description in the docker-compose file to include
   ```
   deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
   ```
**_NOTE:_** This has not been tested with the .NET Spark container.

### Superset
To connect the Apache Superset to the Spark SQL as database, configure with the SQL Alchemy string hive://spark:10000 (unless you've changed the spark container hostname).

#### Known current issue(s)
There is currently some issue stopping Superset from starting correctly. The error message is that the module 'cryptography.hazmat.backends.openssl.x509' can not be found.

**_NOTE:_** There seems to be a bug in pyhive (which is used to be able to connect to Spark SQL) which results in not being able to show the tables in a database, instead
it just shows copies of the database name. To be able to create charts, you will need to use SQL Lab to write queries and then save those results as datasets.

Originally inspired by and adopted from the [3rdman dotnet-spark project](https://github.com/indy-3rdman/docker-dotnet-spark)
