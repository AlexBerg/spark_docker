#!/bin/bash

set +ex

sleep 30

$HIVE_HOME/bin/schematool -dbType mssql -initSchema

sleep 10

$HIVE_HOME/bin/start-metastore &

/usr/bin/tail -f /dev/null