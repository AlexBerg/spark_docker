CREATE DATABASE hive_metastore;
GO
CREATE DATABASE superset;
GO
CREATE LOGIN hive_user WITH PASSWORD='<HIVEUSERSQLPASSWORD>';
GO
CREATE LOGIN superset_user WITH PASSWORD='<SUPERSETUSERSQLPASSWORD>';
GO
USE hive_metastore
GO
CREATE USER hive_user FOR LOGIN hive_user;
GO
ALTER ROLE db_owner ADD MEMBER hive_user;
GO
USE superset
GO
CREATE USER superset_user FOR LOGIN superset_user;
GO
ALTER ROLE db_owner ADD MEMBER superset_user;
GO