#!/bin/bash
# ============================================================
# Database Backup Script
# ============================================================

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_NAME="green_campus_db"
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR"

echo "Creating backup: $BACKUP_FILE"
mysqldump -u root -p "$DB_NAME" > "$BACKUP_FILE"
gzip "$BACKUP_FILE"
echo "Backup saved: ${BACKUP_FILE}.gz"

# Keep only last 10 backups
ls -t "$BACKUP_DIR"/*.gz | tail -n +11 | xargs -r rm
echo "Old backups cleaned."