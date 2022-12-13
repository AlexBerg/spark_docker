#!/bin/bash

set +ex

if [ ! -f /scripts/.init-hive-complete ]; then

    sleep 30

    $HIVE_HOME/bin/schematool -dbType mssql -initSchema

    touch /scripts/.init-hive-complete
else
    echo "Hive already initialized"
fi

sleep 10

$HIVE_HOME/bin/start-metastore &

/usr/bin/tail -f /dev/null