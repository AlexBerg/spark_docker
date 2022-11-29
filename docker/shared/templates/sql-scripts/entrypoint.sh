#Start SQL Server and start script to create hive metastore database and hive user.
/opt/mssql-tools/bin/sqlcmd -S localhost -l 60 -U sa -P "<SAPASSWORD>" -d master -i /usr/src/app/init_metastore.sql &
/opt/mssql/bin/sqlservr