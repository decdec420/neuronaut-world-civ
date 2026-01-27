#!/bin/bash
# Neuronaut World Backup Script
# Creates timestamped backups of the entire project

# Configuration
BACKUP_DIR="$HOME/neuronaut-backups"
PROJECT_DIR="/Users/hackerman/neuronaut-world"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="neuronaut-world-backup-${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Starting Neuronaut World Backup...${NC}"
echo "Timestamp: ${TIMESTAMP}"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Create backup
echo -e "${YELLOW}📦 Creating backup at: ${BACKUP_PATH}${NC}"
rsync -av --progress \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='node_modules/' \
    --exclude='.git/' \
    --exclude='*.db' \
    --exclude='*.sqlite' \
    --exclude='*.log' \
    --exclude='server.pid' \
    --exclude='save_states/' \
    "${PROJECT_DIR}/" "${BACKUP_PATH}/"

# Create compressed archive
echo ""
echo -e "${YELLOW}🗜️  Compressing backup...${NC}"
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"

# Remove uncompressed backup to save space
rm -rf "${BACKUP_NAME}"

# Get size
BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)

echo ""
echo -e "${GREEN}✅ Backup complete!${NC}"
echo -e "${GREEN}📍 Location: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz${NC}"
echo -e "${GREEN}💾 Size: ${BACKUP_SIZE}${NC}"
echo ""

# List recent backups
echo -e "${BLUE}📚 Recent backups:${NC}"
ls -lht "${BACKUP_DIR}" | grep "neuronaut-world-backup" | head -5

# Clean up old backups (keep last 10)
echo ""
echo -e "${YELLOW}🧹 Cleaning up old backups (keeping last 10)...${NC}"
cd "${BACKUP_DIR}"
ls -t neuronaut-world-backup-*.tar.gz | tail -n +11 | xargs -r rm --

echo ""
echo -e "${GREEN}🎉 Backup process complete!${NC}"
