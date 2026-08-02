#!/bin/bash

OPERATION=$1
if [ -z "$OPERATION" ]; then
    echo "❌  No operation requested. Available: groups, ssh"
    exit 1
fi


INSTALLATION_PATH="/opt/mirrorr"

source "$INSTALLATION_PATH/install/helpers.sh"

ensure_bash
ensure_root
ensure_systemd

echo -e "Loading..."

if [ "$OPERATION" = "ssh" ]; then
    IS_UPDATE=1
    do_ssh

    read -p "Mirrorr MUST be restarted for this to take effect. Restart? (Y/n): " RESTART_MIRRORR
    if [[ "$RESTART_MIRRORR" != "N" && "$RESTART_MIRRORR" != "n" ]]; then
        echo "Restarting mirrorr..."
        systemctl restart mirrorr-web
        echo "✔️  All done"
    fi

elif [ "$OPERATION" = "groups" ]; then
    do_groups
    echo "✔️  All done"
    
fi
