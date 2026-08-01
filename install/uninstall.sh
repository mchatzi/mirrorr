#!/bin/bash

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

read -p "This will uninstall Mirrorr. Continue? (Y/n): " DO_UNINSTALL
if [ "$DO_UNINSTALL" != "Y" ]; then
    echo "Not proceeded with uninstall";
    exit 0
fi

#The uninstaller is meant to be loaded from within the installation directory
INSTALLATION_PATH="$(cd "$THIS_SCRIPT_DIR/.." && pwd)"
if [ "$INSTALLATION_PATH" != "/opt/mirrorr" ]; then
  echo "❌  The uninstaller must be loaded from within the installation directory"
  exit 1
fi

#but executed from outside that dir
prevent_runs_from_mirrorr_dir


echo "Uninstalling..."

echo "Unregistering mirrorr service..."
systemctl stop mirrorr-web
systemctl disable mirrorr-web.service
rm /etc/systemd/system/mirrorr-web.service
systemctl daemon-reload

echo "Wiping user and group..."
pkill -u mirrorr
loginctl disable-linger mirrorr
userdel mirrorr
groupdel mirrorr 2>/dev/null || true

read -p "❗️  Save your data? (Y/n): " SAVE_DATA
if [[ "$SAVE_DATA" != "N" && "$SAVE_DATA" != "n" ]]; then
    bak_folder="mirrorr_data"

    if [[ -d "$bak_folder" ]]; then
      for ((i=1;;i++)); do
        if [[ ! -d "mirrorr_data_$i" ]]; then 
          bak_folder="mirrorr_data_$i"
          break
        fi
      done
    fi

    mkdir "$bak_folder" || {
      echo "❌  FATAL: Cannot make $bak_folder! Cannot save data. Unistallation aborted!"
      exit 1
    }
    cd "$bak_folder"

    mv "$INSTALLATION_PATH/data/jobs" .
    mv "$INSTALLATION_PATH/data/logs" .
    mv "$INSTALLATION_PATH/data/ssh" .
    mv "$INSTALLATION_PATH/data/conf.yaml" .

    echo "✔️  Your data has been saved in $(pwd .)"
fi

echo "Wiping installation dir ($INSTALLATION_PATH)"
rm -rf "$INSTALLATION_PATH"

echo -e "\n✔️  Mirrorr has been uninstalled :("
