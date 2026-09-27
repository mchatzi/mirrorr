#!/bin/bash

OPERATION=$1
if [ -z "$OPERATION" ]; then
    echo "❌  No operation requested. Available: groups, ssh, passwd"
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
    fi
    echo "✔️  All done"

elif [ "$OPERATION" = "groups" ]; then
    do_groups

    read -p "Mirrorr MUST be restarted for this to take effect. Restart? (Y/n): " RESTART_MIRRORR
    if [[ "$RESTART_MIRRORR" != "N" && "$RESTART_MIRRORR" != "n" ]]; then
        echo "Restarting mirrorr..."
        systemctl daemon-reload
        systemctl restart mirrorr-web
    fi

    echo "✔️  All done"

elif [ "$OPERATION" = "passwd" ]; then
    do_creds

    read -p "Mirrorr MUST be restarted for this to take effect. Restart? (Y/n): " RESTART_MIRRORR
    if [[ "$RESTART_MIRRORR" != "N" && "$RESTART_MIRRORR" != "n" ]]; then
        echo "Restarting mirrorr..."
        systemctl restart mirrorr-web
    fi
    echo "✔️  All done"

elif [ "$OPERATION" = "sudo" ]; then
    do_sudoers
    echo "✔️  All done"
fi
