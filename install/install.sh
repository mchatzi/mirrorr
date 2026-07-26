#!/bin/bash

set -e
clear
cat <<"EOF"
    __  __
   /  |/  (_)_____________  __________
  / /|_/ / / ___/ ___/ __ \/ ___/ ___/
 / /  / / / /  / /  / /_/ / /  / /
/_/  /_/_/_/  /_/   \____/_/  /_/

EOF

THIS_SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$THIS_SCRIPT_DIR/helpers.sh"


ensure_bash
ensure_root
ensure_systemd

echo -e "Loading..."

IS_UPDATE=0
if [ "$1" = "update" ]; then
    IS_UPDATE=1
fi

#VERSION_TO_INSTALL=$(<"$THIS_SCRIPT_DIR/.version")

INSTALLATION_PATH="/opt/mirrorr"

if [ $IS_UPDATE = 0 ]; then
    if [[ -d "$INSTALLATION_PATH" ]]; then
        echo -e "❌ Installation found at $INSTALLATION_PATH. Are you trying to update?"
        exit 0
    fi

    read -p "This will install Mirrorr. Continue? (Y/n): " DO_INSTALL
    if [ "$DO_INSTALL" = "N" ] || [ "$DO_INSTALL" = "n" ]; then
        echo "❌ Not proceeded with installing"
        exit 0
    fi
else
    prevent_runs_from_mirrorr_dir

    if [[ ! -d "$INSTALLATION_PATH" ]]; then
        echo -e "❌ No installation found at $INSTALLATION_PATH"
        exit 2
    else
        echo -e "✔️ Installation found at $INSTALLATION_PATH"
        
        # TODO 
        # 1. Check and reject updating to older versions (INSTALLED_VERSION > VERSION_TO_INSTALL)
        # 2. Run updaters
        #INSTALLED_VERSION=$(<"$INSTALLATION_PATH/install/.version")
    fi

    read -p "This will update Mirrorr. Continue? (y/N): " DO_UPDATE
    if [ "$DO_UPDATE" != "Y" ] && [ "$DO_UPDATE" != "y" ]; then
        echo "❌ Not proceeded with update";
        exit 0
    fi

    echo -e "Stopping mirrorr..."
    systemctl stop mirrorr-web
fi

echo -e "Installing dependencies..."
do_rsync_and_python_deps

echo "Copying files..."
BASE_DOWNLOADED_DIR="$THIS_SCRIPT_DIR/../"

if [ $IS_UPDATE = 0 ]; then
    mkdir -p "$INSTALLATION_PATH"
    cp -R "$BASE_DOWNLOADED_DIR" "$INSTALLATION_PATH"/
else
    echo "Updating..."
    rsync --archive --quiet --info=stats2 --no-owner --no-perms "$BASE_DOWNLOADED_DIR/" "$INSTALLATION_PATH/"
fi

do_pip_deps

cd "$INSTALLATION_PATH"

chmod +x "$INSTALLATION_PATH/install/install-latest.sh"
chmod +x "$INSTALLATION_PATH/install/install.sh"
chmod +x "$INSTALLATION_PATH/install/uninstall.sh"

do_user_and_groups
do_ssh


#own everything
chown -R mirrorr:mirrorr "$INSTALLATION_PATH"

if [ $IS_UPDATE = 0 ]; then
    register_mirror_service_on_startup
fi

read -p "Start Mirrorr? (Y/n): " START_MIRRORR
if [[ "$START_MIRRORR" != "N" && "$START_MIRRORR" != "n" ]]; then
    echo "Starting application..."
    systemctl start mirrorr-web

    if [ $IS_UPDATE = 0 ]; then
        echo -e "\n✔️ Mirrorr is up and running! Installed at $INSTALLATION_PATH."
    else
        echo -e "\n✔️ Mirrorr has been updated and is up and running!"
    fi
else
    if [ $IS_UPDATE = 0 ]; then
        echo -e "\n✔️ Mirrorr has been installed at $INSTALLATION_PATH. Start with systemctl 'start mirrorr-web'"
    else
        echo -e "\n✔️ Mirrorr has been updated. Start with systemctl 'start mirrorr-web'"
    fi
fi

IP=$(ip a s dev eth0 | awk '/inet / {print $2}' | cut -d/ -f1)
echo -e "Web interface: $IP:5000"
