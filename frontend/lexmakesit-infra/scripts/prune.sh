#!/bin/bash
set -e

# Prune Script
# Usage: ./prune.sh

echo "Starting Docker Prune..."

# Prune images older than 7 days (168h)
docker image prune -a --force --filter "until=168h"

# Prune stopped containers
docker container prune -f

# Prune unused volumes
docker volume prune -f

echo "Docker Prune Completed."
