#!/bin/bash
set -e

# Backup Script
# Usage: ./backup.sh

BACKUP_DIR="/srv/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

mkdir -p "$BACKUP_DIR/postgres"
mkdir -p "$BACKUP_DIR/redis"
mkdir -p "$BACKUP_DIR/qdrant"

echo "Starting Backup: $DATE"

# 1. Postgres Backup
if docker ps | grep -q postgres; then
    echo "Backing up Postgres..."
    docker exec postgres pg_dumpall -U postgres > "$BACKUP_DIR/postgres/pg_dump_$DATE.sql"
    gzip "$BACKUP_DIR/postgres/pg_dump_$DATE.sql"
fi

# 2. Redis Backup
if docker ps | grep -q redis; then
    echo "Backing up Redis..."
    docker exec redis redis-cli save
    docker cp redis:/data/dump.rdb "$BACKUP_DIR/redis/dump_$DATE.rdb"
fi

# 3. Qdrant Backup (Snapshot)
if docker ps | grep -q qdrant; then
    echo "Backing up Qdrant..."
    # Trigger snapshot via API (assuming localhost:6333)
    curl -X POST "http://localhost:6333/collections/my_collection/snapshots"
    # Copy snapshots from volume (requires volume access or cp)
    # For simplicity, we'll assume volume mapping or cp
    # docker cp qdrant:/qdrant/snapshots "$BACKUP_DIR/qdrant/snapshots_$DATE"
fi

# Cleanup Old Backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete

echo "Backup Completed Successfully."
