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


#PYTHON-FLASK
if python3 -c "import flask" &> /dev/null; then
    FLASK_VERSION="$(python3  -c 'import flask; print(flask.__version__)')"
    if dpkg --compare-versions $FLASK_VERSION lt 2.2.2; then
        echo "Required Python Flask version is 2.2.2 or higher, please upgrade!"
        exit 2
    else
        echo "Python Flask version $FLASK_VERSION is installed. Awesome!"
    fi
else
    echo "Python Flask is not installed."
    apt install python3-flask -y
fi

#PYTHON-FLASK-CORS
if python3 -c "import flask_cors" &> /dev/null; then
    FLASK_CORS_VERSION="$(python3  -c 'import flask_cors; print(flask_cors.__version__)')"
    if dpkg --compare-versions $FLASK_CORS_VERSION lt 3.0.10; then
        echo "Required Python Flask CORS version is 3.0.10 or higher, please upgrade!"
        exit 2
    else
        echo "Python Flask CORS version $FLASK_CORS_VERSION is installed. Awesome!"
    fi
else
    echo "Python Flask CORS is not installed."
    apt install python3-flask-cors -y
fi

#PYTHON-YAML
if python3 -c "import yaml" &> /dev/null; then
    YAML_VERSION="$(python3  -c 'import yaml; print(yaml.__version__)')"

    if dpkg --compare-versions $YAML_VERSION lt 6.0; then
        echo "Required Python Yaml version is 6.0 or higher, please upgrade!"
        exit 2
    else
        echo "Python Yaml version $YAML_VERSION is installed. Awesome!"
    fi
else
    echo "Python Yaml is not installed."
    apt install python3-yaml -y
fi

#PYTHON-CRONITER
if python3 -c "import croniter" &> /dev/null; then
    CRONITER_VERSION="$(python3 -c "import importlib.metadata; print(importlib.metadata.version('croniter'))")"

    if dpkg --compare-versions $CRONITER_VERSION lt 2.0.7; then
        echo "Required Python Croniter version is 2.0.7 or higher, please upgrade!"
        exit 2
    else
        echo "Python Croniter version $CRONITER_VERSION is installed. Awesome!"
    fi
else
    echo "Python Croniter is not installed."
    apt install python3-croniter -y
fi

echo "Copying files..."
BASE_DOWNLOADED_DIR="$THIS_SCRIPT_DIR/../"

if [ $IS_UPDATE = 0 ]; then
    mkdir -p "$INSTALLATION_PATH"
    cp -R "$BASE_DOWNLOADED_DIR" "$INSTALLATION_PATH"/
else
    echo "Updating..."
    rsync --archive --quiet --info=stats2 --no-owner --no-perms "$BASE_DOWNLOADED_DIR/" "$INSTALLATION_PATH/"

fi

cd "$INSTALLATION_PATH"

chmod +x "$INSTALLATION_PATH/install/install-latest.sh"
chmod +x "$INSTALLATION_PATH/install/install.sh"
chmod +x "$INSTALLATION_PATH/install/uninstall.sh"

if [ $IS_UPDATE = 0 ]; then
    echo "Creating user and group (mirrorr:mirrorr)..."
    groupadd --system mirrorr
    adduser --system --disabled-login --shell /bin/false --ingroup mirrorr --home $INSTALLATION_PATH/data mirrorr
else
    echo "Application updated..."
fi


while true; do
    read -p "Add mirrorr to group with access to shares (Enter to stop): " ALLOWED_GROUP
    [ -z "$ALLOWED_GROUP" ] && break

    if usermod -aG "$ALLOWED_GROUP" mirrorr; then
        echo "✔️ Added mirrorr to group: $ALLOWED_GROUP"
    else
        echo "❌ Failed to add mirrorr to group: $ALLOWED_GROUP"
    fi
done

if [ ! -d "$INSTALLATION_PATH/data/ssh" ]; then
    mkdir -p "$INSTALLATION_PATH/data/ssh"
fi

do_ssh
chmod 500 "$INSTALLATION_PATH/data/ssh"

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
