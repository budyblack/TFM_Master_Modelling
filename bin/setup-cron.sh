#!/usr/bin/env bash

VENV="./.docker.venv"
PYTHON_BIN="$VENV/bin/python3"

# Define cron job entries
CRON_JOB1="0 * * * * cd $PWD && { \
  export PYTHONPATH=src:$PYTHONPATH; \
  $PYTHON_BIN ./bin/hour_update.py; \
} >> /var/log/cron.log 2>&1"
CRON_JOB2="0 0 * * 0 cd $PWD && { \
  export PYTHONPATH=src:$PYTHONPATH; \
  $PYTHON_BIN ./bin/week_update.py; \
} >> /var/log/cron.log 2>&1"
CRON_JOB3="0 0 1 * * cd $PWD && { \
  export PYTHONPATH=src:$PYTHONPATH; \
  $PYTHON_BIN ./bin/month_update.py; \
} >> /var/log/cron.log 2>&1"


# Function to check and add cron jobs
add_cron_job() {
    local job="$1"
    crontab -l 2>/dev/null | grep -F "$job" >/dev/null
    if [ $? -ne 0 ]; then
        (crontab -l 2>/dev/null; echo "$job") | crontab -
        echo "Added cron job: $job"
    else
        echo "Cron job already exists: $job"
    fi
}

# Add each cron job if it does not exist
add_cron_job "$CRON_JOB1"
add_cron_job "$CRON_JOB2"
add_cron_job "$CRON_JOB3"
echo "Cron job setup completed."
