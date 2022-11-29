minio server /data --console-address ":9001" &

sleep 5

mc alias set myminio http://localhost:9000 <ROOTADMIN> <ROOTPASSWORD>
mc admin user add myminio minio_hive_user <HIVEUSERPASSWORD>
mc mb myminio/hive
mc admin policy set myminio readwrite user=minio_hive_user

# When doing the above in the entrypoint, the docker container exists beliving the server is no longer running (even with nohup).
# Adding the below to shut the server down and restart it to keep the continer (and minio server) going.
mc admin service stop myminio

sleep 2

minio server /data --console-address ":9001"