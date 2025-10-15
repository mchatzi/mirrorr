#!/bin/bash

clear
cat <<"EOF"
    __  __
   /  |/  (_)_____________  __________
  / /|_/ / / ___/ ___/ __ \/ ___/ ___/
 / /  / / / /  / /  / /_/ / /  / /
/_/  /_/_/_/  /_/   \____/_/  /_/

EOF

# Check if the shell is using bash
ensure_bash() {
  if [[ "$(basename "$SHELL")" != "bash" ]]; then
    echo "You need a bash shell to run the uninstaller"
    exit 1
  fi
}

# Run as root only
ensure_root() {
  if [[ "$(id -u)" -ne 0 || $(ps -o comm= -p $PPID) == "sudo" ]]; then
    echo "You need to be root or have sudo rights to run the installer"
    exit 1
  fi
}

ensure_bash
ensure_root

echo -e "Loading..."

INSTALLATION_PATH="/opt/mirrorr"

CURRENT_DIR="$(pwd)"
case "$CURRENT_DIR/" in
    "$INSTALLATION_PATH/"* )
        echo -e "This directory or parent of, will be deleted. Please execute uninstall script from outside of $INSTALLATION_PATH"
        exit 1
        ;;
esac

if [ ! -d "$INSTALLATION_PATH" ]; then
    echo -e "❌ No installation found at $INSTALLATION_PATH"
    exit 1
else
    echo -e "✔️ Installation found at $INSTALLATION_PATH"
fi

read -p "This will uninstall Mirrorr. Continue? (Y/n): " DO_UNINSTALL
if [[ "$DO_UNINSTALL" != "Y" ]]; then
    echo "❌ Not proceeded with uninstall";
    exit 1
fi

echo "Uninstalling..."

echo "Unregistering all mirrorr jobs..."
export XDG_RUNTIME_DIR="/run/user/$(id -u mirrorr)"
su -s /bin/sh mirrorr -c "systemctl --user stop '*.service'"
rm $INSTALLATION_PATH/data/systemd/.config/systemd/user/*.service
rm $INSTALLATION_PATH/data/systemd/.config/systemd/user/*.timer
su -s /bin/sh mirrorr -c "systemctl --user daemon-reload"

echo "Unregistering mirrorr service..."
systemctl stop mirrorr-web.service
rm /etc/systemd/system/mirrorr-web.service
systemctl daemon-reload
systemctl daemon-reexec

echo "Wiping user and group..."
pkill -u mirrorr
loginctl disable-linger mirrorr
userdel mirrorr
groupdel mirrorr 2>/dev/null || true

read -p "Delete your data? (Y/n): " DELETE_DATA
if [[ "$DELETE_DATA" != "Y" ]]; then
    mkdir mirrorr_data
    cd mirrorr_data || exit
    mv "$INSTALLATION_PATH/data/jobs" .
    mv "$INSTALLATION_PATH/data/conf.yaml" .
fi

rm -r $INSTALLATION_PATH

echo -e "\n✔️ Mirrorr has been uninstalled!"
