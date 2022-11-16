minio server /data --console-address ":9001"

mc alias set myminio http://localhost:9000 minio_user minio_password
mc admin user add myminio minio_hive_user Supersecretpassw0rd!
mc mb myminio/hive