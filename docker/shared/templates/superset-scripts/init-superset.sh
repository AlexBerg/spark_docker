set -eo pipefail

export FLASK_APP=superset

superset fab create-admin \
    --username <ADMIN_USER> \
    --firstname <ADMIN_FIRST_NAME> \
    --lastname <ADMIN_LAST_NAME> \
    --password <ADMIN_PWD>

superset db upgrade

superset init

superset runserver -p 8088