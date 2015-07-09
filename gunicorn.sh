#!/bin/bash

# Runs as root to restart nginx service and write to sites-enabled

NAME=nginxify
USER=root
GROUP=root
WORKERS=2
DEPLOY_DIR=/opt

if [[ $1 = "" ]]; then
   LISTEN_ADDR=127.0.0.1
else
   LISTEN_ADDR=0.0.0.0
fi

cd $DEPLOY_DIR

gunicorn $NAME:app -b $LISTEN_ADDR:8888 \
  --name $NAME \
  --workers $WORKERS \
  --user=$USER --group=$GROUP
