CREATE DATABASE hive_metastore;
CREATE USER hive_user WITH PASSWORD '<HIVEUSERSQLPASSWORD>';
ALTER DATABASE hive_metastore OWNER TO hive_user;

CREATE DATABASE superset_metastore;
CREATE USER superset_user WITH PASSWORD '<SUPERSETUSERPASSWORD>';
ALTER DATABASE superset_metastore OWNER TO superset_user;