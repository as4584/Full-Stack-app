#!/bin/bash
"""
AI Receptionist Database Backup System

This script creates daily backups of the PostgreSQL database with rotation.
Prevents data loss and ensures recoverability.

Usage:
    ./backup_database.sh [manual]

Environment:
    - Runs automatically via cron (daily at 2 AM)
    - Manual execution for immediate backup
    - Keeps 30 days of backups
"""

set -euo pipefail

# Configuration
BACKUP_DIR="/home/lex/lexmakesit/backups/database"
CONTAINER_NAME="ai_receptionist_postgres"
DB_NAME="ai_receptionist"
DB_USER="ai_receptionist_user"
RETENTION_DAYS=30
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="ai_receptionist_backup_${TIMESTAMP}.sql"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Ensure backup directory exists
create_backup_directory() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        log "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi
}

# Check if PostgreSQL container is running
check_postgres_running() {
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        error "PostgreSQL container '$CONTAINER_NAME' is not running"
        error "Start it with: cd /home/lex/lexmakesit/backend && docker-compose -f docker-compose.prod.yml up -d postgres"
        exit 1
    fi
    log "PostgreSQL container is running"
}

# Create database backup
create_backup() {
    local backup_path="$BACKUP_DIR/$BACKUP_FILE"
    
    log "Starting database backup..."
    log "Target: $backup_path"
    
    # Create backup using pg_dump inside container
    if docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" > "$backup_path"; then
        
        # Verify backup file was created and has content
        if [[ -f "$backup_path" ]] && [[ -s "$backup_path" ]]; then
            local backup_size=$(du -h "$backup_path" | cut -f1)
            success "Database backup created: $backup_path ($backup_size)"
            
            # Compress backup to save space
            log "Compressing backup..."
            gzip "$backup_path"
            local compressed_size=$(du -h "${backup_path}.gz" | cut -f1)
            success "Backup compressed: ${backup_path}.gz ($compressed_size)"
            
            return 0
        else
            error "Backup file is empty or was not created properly"
            return 1
        fi
    else
        error "pg_dump command failed"
        return 1
    fi
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days..."
    
    local deleted_count=0
    
    # Find and delete old backup files
    while IFS= read -r -d '' backup_file; do
        rm "$backup_file"
        deleted_count=$((deleted_count + 1))
        log "Deleted old backup: $(basename "$backup_file")"
    done < <(find "$BACKUP_DIR" -name "ai_receptionist_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -print0)
    
    if [[ $deleted_count -gt 0 ]]; then
        success "Cleaned up $deleted_count old backup(s)"
    else
        log "No old backups to clean up"
    fi
    
    # Show current backup status
    local backup_count=$(find "$BACKUP_DIR" -name "ai_receptionist_backup_*.sql.gz" -type f | wc -l)
    local total_size=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "0")
    log "Current backups: $backup_count files, total size: $total_size"
}

# Verify backup integrity
verify_backup() {
    local latest_backup=$(find "$BACKUP_DIR" -name "ai_receptionist_backup_*.sql.gz" -type f -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
    
    if [[ -n "$latest_backup" ]]; then
        log "Verifying backup integrity: $(basename "$latest_backup")"
        
        # Check if gzip file is valid
        if gzip -t "$latest_backup" 2>/dev/null; then
            success "Backup integrity check passed"
            return 0
        else
            error "Backup integrity check failed - corrupted file"
            return 1
        fi
    else
        error "No backup files found to verify"
        return 1
    fi
}

# Main backup process
main() {
    local manual_run=false
    
    if [[ $# -gt 0 ]] && [[ "$1" == "manual" ]]; then
        manual_run=true
        log "Manual backup requested"
    else
        log "Automated backup started (via cron)"
    fi
    
    echo "=================================================="
    echo "🗄️  AI RECEPTIONIST DATABASE BACKUP"
    echo "   Date: $(date)"
    echo "   Mode: $(if $manual_run; then echo "Manual"; else echo "Automated"; fi)"
    echo "=================================================="
    
    # Run backup process
    create_backup_directory
    check_postgres_running
    
    if create_backup; then
        cleanup_old_backups
        
        if verify_backup; then
            echo "=================================================="
            success "DATABASE BACKUP COMPLETED SUCCESSFULLY"
            echo "   📁 Location: $BACKUP_DIR"
            echo "   📅 Retention: $RETENTION_DAYS days"
            echo "   ✅ Automatic rotation enabled"
            echo "=================================================="
        else
            warning "Backup created but verification failed"
        fi
    else
        error "BACKUP FAILED"
        exit 1
    fi
}

# Install cron job for automated backups (run once)
install_cron_job() {
    local script_path=$(realpath "$0")
    local cron_line="0 2 * * * $script_path >/dev/null 2>&1"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "$script_path"; then
        log "Cron job already installed"
    else
        log "Installing daily backup cron job..."
        (crontab -l 2>/dev/null; echo "$cron_line") | crontab -
        success "Cron job installed: Daily backups at 2:00 AM"
    fi
}

# Check arguments for special commands
if [[ $# -gt 0 ]]; then
    case "$1" in
        "install-cron")
            install_cron_job
            exit 0
            ;;
        "verify")
            verify_backup
            exit $?
            ;;
        "cleanup")
            cleanup_old_backups
            exit 0
            ;;
        "manual")
            main "$@"
            exit $?
            ;;
        *)
            echo "Usage: $0 [manual|install-cron|verify|cleanup]"
            exit 1
            ;;
    esac
else
    main "$@"
fi