#!/bin/bash

# Ensure the script receives specific arguments
if [ $# -ne 9 ]; then
    echo "Usage: $0 <schedule_scope: user|system> <job_name> <job_schedule> <application_root_abs_path> <job_conf_abs_path> <mirrorr_conf_abs_path> <log_level> <job_logs_dir> <group>"
    exit 1
fi

# Parameters from command-line input
ARG_JOB_SCHEDULE_SCOPE=$1
ARG_JOB_NAME=$2
ARG_JOB_SCHEDULE=$3
ARG_APPLICATION_ROOT=$4
ARG_JOB_CONF_FILE=$5
ARG_MIRRORR_CONF_FILE=$6
ARG_LOG_LEVEL=$7
ARG_JOB_LOGS_DIR=$8
ARG_GROUP=$9

# Determine the file locations based on schedule scope
if [ "$ARG_JOB_SCHEDULE_SCOPE" = "user" ]; then
    user_home=$(eval echo ~$USER)
    UNIT_DIR="$user_home/.config/systemd/user"
elif [ "$ARG_JOB_SCHEDULE_SCOPE" = "system" ]; then
    UNIT_DIR="/etc/systemd/system"
else
    echo "Invalid schedule scope. Use 'user' or 'system'."
    exit 1
fi


# Create the service and timer files
UNIT_NAME=$(echo "$ARG_JOB_NAME" | tr ' ' '_')
SERVICE_FILE="$UNIT_DIR/$UNIT_NAME.service"
TIMER_FILE="$UNIT_DIR/$UNIT_NAME.timer"


if [ -f "$TIMER_FILE" ] || [ -f "$SERVICE_FILE" ]; then
    echo "⏭️  Timer or service already exists for '$UNIT_NAME'. Skipping creation."
    exit 1

else
    echo "✅ Creating systemd service and timer for '$UNIT_NAME'..."
    mkdir -p "$UNIT_DIR"

    IP=$(ip a s dev eth0 | awk '/inet / {print $2}' | cut -d/ -f1)
    command_with_quotes="python3 \"$ARG_APPLICATION_ROOT/sys/mirrorr.py\" -conf \"$ARG_MIRRORR_CONF_FILE\" -job \"$ARG_JOB_CONF_FILE\" -loglevel $ARG_LOG_LEVEL -ip $IP -logsdir \"$ARG_JOB_LOGS_DIR\""
    shell_ready_command=$(bash -c "printf '%q ' $command_with_quotes")
    COMMAND_FOR_EXECSTART=$(echo ${shell_ready_command} | sed 's/\\/\\\\/g')

    if [ -n "$ARG_GROUP" ]; then
        USE_GROUP="Group=$ARG_GROUP"
    else
        USE_GROUP=""
    fi

    cat > "$SERVICE_FILE" <<EOL
[Unit]
Description=$ARG_JOB_NAME

[Service]
Type=oneshot
ExecStart=/bin/bash -c "$COMMAND_FOR_EXECSTART"
$USE_GROUP
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


