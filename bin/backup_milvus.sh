#!/usr/bin/env bash
source .env
cd bin
if [ ! -f milvus-backup ]; then
    wget https://github.com/zilliztech/milvus-backup/releases/download/v0.4.27/milvus-backup_Linux_x86_64.tar.gz
    tar xzvf milvus-backup_Linux_x86_64.tar.gz
    rm README.md
    rm LICENSE
    rm milvus-backup_Linux_x86_64.tar.gz
fi
echo "****************** Removing old backup"
./milvus-backup delete -n milvus_backup
echo "****************** Creating new backup"
./milvus-backup create -n milvus_backup
cd ..
echo "****************** Packaging new backup"
cd volumes/minio
tar czf ../../milvus_backup.tar.gz a-bucket/backup/milvus_backup
cd ../..
#tar czf milvus_backup.tar.gz volumes/minio/a-bucket/backup/milvus_backup
echo "****************** Uploading new backup to SACO"
curl -u $SACO_USER:$SACO_PASSWORD -T milvus_backup.tar.gz https://saco.csic.es/remote.php/dav/files/43435205G/data/MinkaAnalyst/milvus_backup.tar.gz
