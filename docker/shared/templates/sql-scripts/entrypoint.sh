#!/bin/bash

if [ ! -f /scripts/.init-databases-complete ]; then
    #Start SQL Server and start script to create hive metastore database and hive user.
    /opt/mssql-tools/bin/sqlcmd -S localhost -l 60 -U sa -P "<SAPASSWORD>" -d master -i /scripts/init_databases.sql &

    touch /scripts/.init-databases-complete
else
    echo "Databases already initialized"
fi
/opt/mssql/bin/sqlservr