nohup minio server /data --console-address ":9001" &

sleep 5

mc alias set myminio http://localhost:9000 <ROOTADMIN> <ROOTPASSWORD>
mc admin user add myminio minio_hive_user <HIVEUSERPASSWORD>
mc mb myminio/hive
mc admin policy set myminio readwrite user=minio_hive_user