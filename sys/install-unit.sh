#!/bin/bash

#########################################################################################
#
#  EXAMPLE USAGE
# 
#  Every 20 mins, and double quotes where needed
#  ./install.sh user "TV Bak" "*:0/20" "/some/path/with spaces/" /dest/path/ 24
#  
#  NOT SURE ABOUT THE BACKSLASH ESCAPING HERE: printf '%q ' seems to breaking this (creates \\\)
#  Every 1 minute, and backslash escaping where needed
#  ./install.sh system TV\ Bak "*-*-* *:*:00" /some/path/with\ spaces/ /dest/path/ 24
#
##########################################################################################

# Ensure the script receives specific arguments
if [ $# -ne 7 ]; then
    echo "Usage: $0 <schedule_scope: user|system> <job_name> <job_schedule> <job_conf_abs_path> <mirrorr_conf_abs_path> <log_level> <job_logs_dir>"
    exit 1
fi

# Parameters from command-line input
ARG_JOB_SCHEDULE_SCOPE=$1
ARG_JOB_NAME=$2
ARG_JOB_SCHEDULE=$3
ARG_JOB_CONF_FILE=$4
ARG_MIRRORR_CONF_FILE=$5
ARG_LOG_LEVEL=$6
ARG_JOB_LOGS_DIR=$7

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
    command_with_quotes="python3 /root/mirrorr/sys/mirrorr.py -conf \"$ARG_MIRRORR_CONF_FILE\" -job \"$ARG_JOB_CONF_FILE\" -loglevel $ARG_LOG_LEVEL -ip $IP -logsdir \"$ARG_JOB_LOGS_DIR\""
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


