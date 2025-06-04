#!/usr/bin/env bash

# Define file path and script
UPDATE_HOUR_SCRIPT="bin/hour_update.py"
SUMMARY_WEEK_FILE="summaries/week_summary_esp.txt"
UPDATE_WEEK_SCRIPT="bin/week_update.py"
SUMMARY_MONTH_FILE="summaries/month_summary_esp.txt"
UPDATE_MONTH_SCRIPT="bin/month_update.py"

# Function to check if week_summary.txt needs an update
check_and_update() {
    mkdir -p summaries
    mkdir -p tmp
    #Hour update
    ./"$UPDATE_HOUR_SCRIPT"
    #Week update
    if [ ! -f ./"$SUMMARY_WEEK_FILE" ]; then
        echo "File $SUMMARY_WEEK_FILE does not exist. Running update script."
        ./"$UPDATE_WEEK_SCRIPT"
        echo "File created correctly."
    else
        LAST_MODIFIED=$(stat -c %Y ./"$SUMMARY_WEEK_FILE")
        LAST_SUNDAY=$(date -d "00:00 last sunday" +%s)
        
        if [ "$LAST_MODIFIED" -lt "$LAST_SUNDAY" ]; then
            echo "File $SUMMARY_WEEK_FILE is outdated. Running update script."
            ./"$UPDATE_WEEK_SCRIPT"
            echo "File created correctly."
        else
            echo "File $SUMMARY_WEEK_FILE is up to date. No need to run update script."
        fi
    fi
    #Month update
    if [ ! -f ./"$SUMMARY_MONTH_FILE" ]; then
        echo "File $SUMMARY_MONTH_FILE does not exist. Running update script."
        ./"$UPDATE_MONTH_SCRIPT"
        echo "File created correctly."
    else
        LAST_MODIFIED=$(stat -c %Y ./"$SUMMARY_MONTH_FILE")
        FIRST_DAY_OF_MONTH=$(date -d "$(date +%Y-%m-01)" +%s)
        
        if [ "$LAST_MODIFIED" -lt "$FIRST_DAY_OF_MONTH" ]; then
            echo "File $SUMMARY_MONTH_FILE is outdated. Running update script."
            ./"$UPDATE_MONTH_SCRIPT"
            echo "File created correctly."
        else
            echo "File $SUMMARY_MONTH_FILE is up to date. No need to run update script."
        fi
    fi
}

# Run check and update function
check_and_update