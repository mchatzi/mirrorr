#!/bin/bash

if [ $# -ne 7 ]; then
    echo "Usage: $0 <job_name> <job_schedule> <application_root_abs_path> <job_conf_abs_path> <mirrorr_conf_abs_path> <log_level> <job_logs_dir>"
    exit 1
fi

ARG_JOB_NAME=$1
ARG_JOB_SCHEDULE=$2
ARG_APPLICATION_ROOT=$3
ARG_JOB_CONF_FILE=$4
ARG_MIRRORR_CONF_FILE=$5
ARG_LOG_LEVEL=$6
ARG_JOB_LOGS_DIR=$7

UNIT_DIR="$HOME/.config/systemd/user"

# Create the service and timer files
UNIT_NAME=$(echo "$ARG_JOB_NAME" | tr ' ' '_')
SERVICE_FILE="$UNIT_DIR/$UNIT_NAME.service"
TIMER_FILE="$UNIT_DIR/$UNIT_NAME.timer"


if [ -f "$TIMER_FILE" ] || [ -f "$SERVICE_FILE" ]; then
    echo "⏭️  Timer or service already exists for '$UNIT_NAME'. Skipping creation."
    exit 1

else
    echo "✅ Creating service and timer for $UNIT_DIR/$UNIT_NAME..."

    FQDN_OR_IP=$(hostname -f 2>/dev/null)
    if [ -z "$FQDN_OR_IP" ] || [[ "$FQDN_OR_IP" == *"Name or service not known"* ]] || [[ "$FQDN_OR_IP" != *.* ]]; then
        FQDN_OR_IP=$(ip a s dev eth0 | awk '/inet / {print $2}' | cut -d/ -f1)
    fi

    command_with_quotes="python3 \"$ARG_APPLICATION_ROOT/sys/mirrorr.py\" -conf \"$ARG_MIRRORR_CONF_FILE\" -job \"$ARG_JOB_CONF_FILE\" -loglevel $ARG_LOG_LEVEL -fqdn_or_ip $FQDN_OR_IP -logsdir \"$ARG_JOB_LOGS_DIR\""
    shell_ready_command=$(bash -c "printf '%q ' $command_with_quotes")
    COMMAND_FOR_EXECSTART=$(echo ${shell_ready_command} | sed 's/\\/\\\\/g')

    cat > "$SERVICE_FILE" <<EOL
[Unit]
Description=$ARG_JOB_NAME

[Service]
Type=oneshot
ExecStart=/bin/bash -c "$COMMAND_FOR_EXECSTART"
EOL

    cat > "$TIMER_FILE" <<EOL
[Unit]
Description=Schedule $ARG_JOB_NAME

[Timer]
OnCalendar=$ARG_JOB_SCHEDULE
Persistent=true

[Install]
WantedBy=timers.target
EOL

fi

echo "Installed '$ARG_JOB_NAME'"


