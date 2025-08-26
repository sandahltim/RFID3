#!/bin/bash
# Setup script for automated contract snapshots
# Version: 2025-08-24-v1

echo "Setting up automated contract snapshots..."

# Determine project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

# Create necessary directories
mkdir -p "$PROJECT_DIR/logs"

# Create the cron entry
CRON_ENTRY="# RFID3 Contract Snapshots - Wed/Fri at 7 AM
0 7 * * 3,5 cd $PROJECT_DIR && $PROJECT_DIR/venv/bin/python3 scripts/create_weekly_snapshots.py >> logs/snapshot_cron.log 2>&1"

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "create_weekly_snapshots.py"; then
    echo "⚠️  Cron entry already exists. Current cron jobs:"
    crontab -l | grep -A1 -B1 "create_weekly_snapshots.py"
else
    # Add to cron
    (crontab -l 2>/dev/null; echo ""; echo "$CRON_ENTRY") | crontab -
    echo "✅ Added cron job for contract snapshots"
    echo "   Schedule: Wednesdays and Fridays at 7:00 AM"
fi

# Test the script
echo ""
echo "🧪 Testing snapshot script..."
cd "$PROJECT_DIR"
"$PROJECT_DIR/venv/bin/python3" scripts/create_weekly_snapshots.py --test 2>&1 | head -10

echo ""
echo "📋 Setup complete! Contract snapshots will run:"
echo "   • Every Wednesday at 7:00 AM"
echo "   • Every Friday at 7:00 AM"
echo ""
echo "📁 Log files:"
echo "   • $PROJECT_DIR/logs/snapshot_automation.log (detailed logs)"
echo "   • $PROJECT_DIR/logs/snapshot_cron.log (cron output)"
echo "   • $PROJECT_DIR/logs/last_snapshot_run.json (status summary)"
echo ""
echo "🔧 To check status: cat $PROJECT_DIR/logs/last_snapshot_run.json"
echo "🔧 To run manually: cd $PROJECT_DIR && ./scripts/create_weekly_snapshots.py"