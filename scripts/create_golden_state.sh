#!/bin/bash
# Golden State Backup - Saves working production state
# Run this after verifying everything works perfectly

set -e

SERVER="Innovation"
BACKUP_DIR="/opt/ai-receptionist/golden-state-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="golden_state_${TIMESTAMP}"

echo "💾 Creating Golden State Backup: $BACKUP_NAME"
echo "=============================================="

# Create backup directory on server
ssh $SERVER "mkdir -p $BACKUP_DIR/$BACKUP_NAME"

# Backup frontend Docker images
echo "📦 Backing up Docker images..."
ssh $SERVER "
    docker save dashboard_nextjs_prod:latest | gzip > $BACKUP_DIR/$BACKUP_NAME/dashboard_image.tar.gz
    docker save auth_nextjs_prod:latest | gzip > $BACKUP_DIR/$BACKUP_NAME/auth_image.tar.gz
    docker save ai-receptionist-app-1:latest | gzip > $BACKUP_DIR/$BACKUP_NAME/backend_image.tar.gz
"

# Backup source code
echo "📁 Backing up source code..."
ssh $SERVER "
    tar -czf $BACKUP_DIR/$BACKUP_NAME/frontend_code.tar.gz -C /opt/ai-receptionist frontend/
    tar -czf $BACKUP_DIR/$BACKUP_NAME/auth_code.tar.gz -C /opt/ai-receptionist auth-frontend/
    tar -czf $BACKUP_DIR/$BACKUP_NAME/backend_code.tar.gz -C /opt/ai-receptionist backend/
"

# Backup Caddy config
echo "🔧 Backing up Caddy configuration..."
ssh $SERVER "sudo cp /etc/caddy/Caddyfile $BACKUP_DIR/$BACKUP_NAME/Caddyfile"

# Backup database
echo "🗄️  Backing up database..."
ssh $SERVER "
    cd /opt/ai-receptionist/backend && \
    docker compose exec -T postgres pg_dump -U postgres ai_receptionist > $BACKUP_DIR/$BACKUP_NAME/database_backup.sql
"

# Create metadata file
echo "📝 Creating metadata..."
ssh $SERVER "cat > $BACKUP_DIR/$BACKUP_NAME/metadata.json << 'EOF'
{
  \"backup_name\": \"$BACKUP_NAME\",
  \"timestamp\": \"$TIMESTAMP\",
  \"created_by\": \"$USER\",
  \"containers\": {
    \"dashboard\": \"$(ssh $SERVER 'docker inspect dashboard_nextjs_prod --format {{.Id}}')\",
    \"auth\": \"$(ssh $SERVER 'docker inspect auth_nextjs_prod --format {{.Id}}')\",
    \"backend\": \"$(ssh $SERVER 'docker inspect ai-receptionist-app-1 --format {{.Id}}')\"
  },
  \"description\": \"Golden state backup - all services working\"
}
EOF
"

# Create restore script
ssh $SERVER "cat > $BACKUP_DIR/$BACKUP_NAME/restore.sh << 'EOF'
#!/bin/bash
set -e
echo \"🔄 Restoring Golden State: $BACKUP_NAME\"
cd $BACKUP_DIR/$BACKUP_NAME
docker load < dashboard_image.tar.gz
docker load < auth_image.tar.gz
docker load < backend_image.tar.gz
cd /opt/ai-receptionist/frontend && docker compose -f docker-compose.prod.yml up -d
cd /opt/ai-receptionist/auth-frontend && docker compose -f docker-compose.prod.yml up -d
cd /opt/ai-receptionist/backend && docker compose up -d
sudo cp Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy
echo \"✅ Golden State Restored!\"
EOF
chmod +x $BACKUP_DIR/$BACKUP_NAME/restore.sh
"

# Set as latest golden state
ssh $SERVER "ln -sf $BACKUP_DIR/$BACKUP_NAME $BACKUP_DIR/latest"

echo ""
echo "✅ Golden State Backup Complete!"
echo ""
echo "Backup location: $SERVER:$BACKUP_DIR/$BACKUP_NAME"
echo ""
echo "To restore this state:"
echo "  ssh $SERVER 'bash $BACKUP_DIR/$BACKUP_NAME/restore.sh'"
echo ""
echo "To restore latest golden state:"
echo "  ssh $SERVER 'bash $BACKUP_DIR/latest/restore.sh'"
