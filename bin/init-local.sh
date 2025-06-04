#!/usr/bin/env bash
if [ "$#" -eq 1 ] 
then
    export VENV=.docker.venv
else
    export VENV=.venv
fi
if [[ ! -d ${VENV} ]]; then
    python3 -m venv ${VENV}
    echo "Created virtual environment"
fi
export BPM_GID=`id -g`
export BPM_UID=`id -u`
export BPM_PORT=13000
export MINIO_PORT_9000=9000
export MINIO_PORT_9001=9001
export MILVUS_PORT_19530=19530
export MILVUS_PORT_9091=9091
source ${VENV}/bin/activate
pip install -U pip
pip install -r requirements.txt
export PYTHONPATH=${PWD}/src:$PYTHONPATH
source .env
