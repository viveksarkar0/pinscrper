#!/bin/bash

# Setup script for Pinterest scraper cron job
# This script sets up a daily cron job to run the Pinterest scraper

echo "Setting up Pinterest scraper cron job..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3)
CRON_SCRIPT="$SCRIPT_DIR/cron_scraper.py"

# Make the cron script executable
chmod +x "$CRON_SCRIPT"

# Create a wrapper script that sets up the environment
WRAPPER_SCRIPT="$SCRIPT_DIR/run_cron_scraper.sh"
cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash
# Wrapper script for cron job

# Set environment variables
export PATH=/usr/local/bin:/usr/bin:/bin
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the scraper
$PYTHON_PATH "$CRON_SCRIPT" >> cron_output.log 2>&1
EOF

chmod +x "$WRAPPER_SCRIPT"

# Add cron job (runs daily at 2 AM)
CRON_JOB="0 2 * * * $WRAPPER_SCRIPT"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$WRAPPER_SCRIPT"; then
    echo "Cron job already exists. Updating..."
    # Remove existing job and add new one
    (crontab -l 2>/dev/null | grep -v "$WRAPPER_SCRIPT"; echo "$CRON_JOB") | crontab -
else
    echo "Adding new cron job..."
    # Add new job to existing crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
fi

echo "Cron job setup complete!"
echo "The scraper will run daily at 2:00 AM"
echo "Logs will be saved to: $SCRIPT_DIR/cron_output.log"
echo ""
echo "To view current cron jobs: crontab -l"
echo "To remove the cron job: crontab -e (then delete the line)"
echo ""
echo "IMPORTANT: Please update board_urls.json with your actual Pinterest board URLs"
