#!/usr/bin/env bash
curl https://saco.csic.es/s/sX7aS2NzMbL52bN/download?milvus_backup.tar.gz -o milvus_backup.tar.gz
unzip milvus_backup.tar.gz
cp MinkaAnalyst/milvus_backup.tar.gz .
rm -rf MinkaAnalyst
docker compose exec minio tar xzvf mnt/milvus_backup.tar.gz -C /minio_data
##docker compose exec minio mv volumes/minio/a-bucket minio-data
##sudo tar xzvf milvus_backup.tar.gz
cd bin
if [ ! -f milvus-backup ]; then
    wget https://github.com/zilliztech/milvus-backup/releases/download/v0.4.27/milvus-backup_Linux_x86_64.tar.gz
    tar xzvf milvus-backup_Linux_x86_64.tar.gz
    rm README.md
    rm LICENSE
    rm milvus-backup_Linux_x86_64.tar.gz
fi
./env_yaml.py configs/backup.schema.yaml configs/backup.yaml
./milvus-backup restore --drop_exist_collection --drop_exist_index -n milvus_backup
cd ..
