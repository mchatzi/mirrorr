#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <schedule_scope: user|system> <job_description>"
    exit 1
fi

SCHEDULE_SCOPE=$1
JOB_DESCRIPTION=$2

if [ "$SCHEDULE_SCOPE" = "user" ]; then
    UNIT_DIR="$HOME/.config/systemd/user"
    SYSTEMCTL_CMD="systemctl --user"
elif [ "$SCHEDULE_SCOPE" = "system" ]; then
    UNIT_DIR="/etc/systemd/system"
    SYSTEMCTL_CMD="systemctl"
else
    echo "Invalid schedule scope."
    exit 1
fi

UNIT_NAME=$(echo "$JOB_DESCRIPTION" | tr ' ' '_')
SERVICE_FILE="$UNIT_DIR/$UNIT_NAME.service"
TIMER_FILE="$UNIT_DIR/$UNIT_NAME.timer"

$SYSTEMCTL_CMD stop "$UNIT_NAME.timer"
$SYSTEMCTL_CMD disable "$UNIT_NAME.timer"

echo "Removing $SERVICE_FILE"
echo "Removing $TIMER_FILE"
rm -f "$SERVICE_FILE" "$TIMER_FILE"

$SYSTEMCTL_CMD daemon-reexec

echo "🧹 Uninstalled $JOB_DESCRIPTION"
