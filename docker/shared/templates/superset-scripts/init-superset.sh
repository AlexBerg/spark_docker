export FLASK_APP=superset

echo 'Running database upgrade'

superset db upgrade

echo 'Creating admin'

superset fab create-admin \
    --username <ADMIN_USER> \
    --firstname <ADMIN_FIRST_NAME> \
    --lastname <ADMIN_LAST_NAME> \
    --password <ADMIN_PWD>

echo 'Running init'

superset init

echo 'Starting development server'

superset run -p 8088 --with-treads --reload --host=8088