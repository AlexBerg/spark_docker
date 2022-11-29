CREATE DATABASE hive_metastore;
GO
CREATE LOGIN hive_user WITH PASSWORD='<HIVEUSERSQLPASSWORD>';
GO
USE hive_metastore
GO
CREATE USER hive_user FOR LOGIN hive_user;
GO
ALTER ROLE db_owner ADD MEMBER hive_user;
GO