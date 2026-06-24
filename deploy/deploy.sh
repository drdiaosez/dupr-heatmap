#!/bin/bash
# deploy.sh — sync public/ to your DigitalOcean droplet
#
# Usage: ./deploy.sh
# First run: make sure you've run `ssh-copy-id root@YOUR_DROPLET_IP` so this is passwordless.

set -e

DROPLET_IP="67.205.139.219"
DROPLET_USER="bot"
REMOTE_PATH="/var/www/dupr-heatmap"
LOCAL_PATH="$(cd "$(dirname "$0")/.." && pwd)/public"

echo "Deploying $LOCAL_PATH → $DROPLET_USER@$DROPLET_IP:$REMOTE_PATH"

rsync -avz --delete \
  --exclude='.DS_Store' \
  "$LOCAL_PATH/" \
  "$DROPLET_USER@$DROPLET_IP:$REMOTE_PATH/"

echo "Done! Visit http://$DROPLET_IP or your domain."
