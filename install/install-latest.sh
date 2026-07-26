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


printf "Welcome to Mirrorr online installer.\nThis program will guide you through the install/update process. Proceed? (Y/n): "
read -r PROCEED
if [[ "$PROCEED" = "N" || "$PROCEED" = "n" ]]; then
    printf "\n❌ Not proceeded with installing\n"
    exit 1
fi

if [[ "$(id -u)" -ne 0 || $(ps -o comm= -p $PPID) == "sudo" ]]; then
    printf "\nYou need to be root or have sudo rights to run the installer\n"
    exit 1
fi


cleanup() {
    status=$?

    if [[ -n "$THIS_SCRIPT_DIR" && -d "$THIS_SCRIPT_DIR" ]]; then
        cd "$THIS_SCRIPT_DIR" 2>/dev/null
        rm -rf "$TEMP_INSTALL_DIR"
    fi

    if [[ $status -eq 1 && $OPERATION -ne 3 ]]; then
        printf "\n\n⚠ Install/update did not succeed and was interrupted ⚠\n"
        echo "You may want to run the uninstaller at $INSTALLATION_PATH/install/uninstall.sh to clean up before retrying"
    fi
}

trap cleanup EXIT


while true; do
    printf "\nPlease select an option. \n\t[1] Install latest version\n\t[2] Update to latest version\n\t[3] Uninstall\n\t[4] Cancel\n\t> "
    read -r OPERATION
    if [[ "$OPERATION" = [1-4] ]]; then
        break
    fi
done

printf "\n"

if [ $OPERATION = 4 ]; then
    exit 0
fi

INSTALLATION_PATH="/opt/mirrorr"

if [ $OPERATION = 3 ]; then
    UNINSTALLER="$INSTALLATION_PATH/install/uninstall.sh"
    if [ ! -f "$UNINSTALLER" ]; then
        #legacy installs?
        UNINSTALLER="$INSTALLATION_PATH/uninstall.sh"
    fi

    if [ -f "$UNINSTALLER" ]; then
        chmod +x "$UNINSTALLER"
        bash -c "$UNINSTALLER"
    else
        echo "No local uninstaller found!"
        exit 1
    fi
else
    THIS_SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
    TEMP_INSTALL_DIR="$THIS_SCRIPT_DIR/.temp"
    mkdir "$TEMP_INSTALL_DIR"
    cd "$TEMP_INSTALL_DIR"

    echo "Downloading latest version of Mirrorr.."

    LATEST_TAG_VERSION="$(wget -qLO - https://api.github.com/repos/mchatzi/mirrorr/releases/latest | grep tag_name | cut -d '"' -f 4).tar.gz"
    LATEST_TAG_URL="https://github.com/mchatzi/mirrorr/archive/refs/tags/$LATEST_TAG_VERSION"
    wget -O latest.tar.gz $LATEST_TAG_URL || {
        echo "❌ Download failed";
        FAILED=1
    }

    if [ -z $FAILED ]; then
        tar -xzf latest.tar.gz || {
            echo "❌ Extraction failed";
            FAILED=1
        }
    fi

    if [ -z $FAILED ]; then
        FOLDER_NAME=$(find . -mindepth 1 -maxdepth 1 -type d | head -n 1)
        if [ ! -d "$FOLDER_NAME" ]; then
            echo "❌ Expected folder '$FOLDER_NAME' not found"
            FAILED=1
        fi
    fi

    if [ -z $FAILED ]; then
        cd "./$FOLDER_NAME"
        chmod +x install/install.sh
        if [ $OPERATION = 1 ]; then
            install/install.sh
        elif [ $OPERATION = 2 ]; then
            install/install.sh update
        fi
    # fi
fi


