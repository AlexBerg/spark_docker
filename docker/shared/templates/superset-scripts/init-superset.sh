#!/bin/bash

export FLASK_APP=superset

if [ ! -f /scripts/.init-superset-complete ]; then

    echo 'Running database upgrade'

    superset db upgrade

    echo 'Creating admin'

    superset fab create-admin \
        --username <ADMIN_USER> \
        --firstname <ADMIN_FIRST_NAME> \
        --lastname <ADMIN_LAST_NAME> \
        --password <ADMIN_PWD> \
        --email <ADMIN_EMAIL>

    echo 'Running init'

    superset init

    touch /scripts/.init-superset-complete
else
    echo 'Superset already initialized. Running database upgrade' 

    superset db upgrade
fi


echo 'Starting development server'

superset run -p 8088 --with-threads --reload --host=0.0.0.0