#!/bin/bash

set +ex

sleep 30

$HIVE_HOME/bin/schematool -dbType mssql -initSchema

sleep 10

$HIVE_HOME/bin/hive --service metastore &

sleep 10

$HIVE_HOME/bin/hiveserver2 --hiveconf hive.root.logger=Info,console &

/usr/bin/tail -f /dev/null