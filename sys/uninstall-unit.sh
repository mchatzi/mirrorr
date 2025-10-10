#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <job_description>"
    exit 1
fi

JOB_DESCRIPTION=$1

UNIT_DIR="$HOME/.config/systemd/user"

UNIT_NAME=$(echo "$JOB_DESCRIPTION" | tr ' ' '_')
SERVICE_FILE="$UNIT_DIR/$UNIT_NAME.service"
TIMER_FILE="$UNIT_DIR/$UNIT_NAME.timer"

systemctl --user stop "$UNIT_NAME.timer"
systemctl --user disable "$UNIT_NAME.timer"

echo "Removing $SERVICE_FILE"
echo "Removing $TIMER_FILE"
rm -f "$SERVICE_FILE" "$TIMER_FILE"

systemctl --user daemon-reexec

echo "🧹 Uninstalled $JOB_DESCRIPTION"
