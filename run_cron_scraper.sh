#!/bin/bash
# Wrapper script for cron job

# Set environment variables
export PATH=/usr/local/bin:/usr/bin:/bin
cd "/Users/viveksarkar/webscrperinterest"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the scraper
/Users/viveksarkar/webscrperinterest/venv/bin/python3 "/Users/viveksarkar/webscrperinterest/cron_scraper.py" >> cron_output.log 2>&1
