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
    echo "You need a bash shell to run the installer"
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

echo -e "Loading..."
ensure_bash
ensure_root

INSTALLATION_PATH="/opt/mirrorr"

CURRENT_DIR="$(pwd)"
case "$CURRENT_DIR/" in
    "$INSTALLATION_PATH/"* )
        echo -e "This directory or parent of, will be updated. Please execute update script from outside of $INSTALLATION_PATH or via the online source (bash -c \"$(wget -qLO - wget -qLO - https://raw.githubusercontent.com/mchatzi/mirrorr/refs/heads/main/update.sh)\")"
        exit 1
        ;;
esac

if [ ! -d "$INSTALLATION_PATH" ]; then
    echo -e "❌ No installation found at $INSTALLATION_PATH"
    exit 1
else
    echo -e "✔️ Installation found at $INSTALLATION_PATH"
fi

read -p "This will update Mirrorr. Continue? (y/N): " DO_UPDATE
if [[ "$DO_UPDATE" != "Y" ]] && [[ "$DO_UPDATE" != "y" ]]; then
    echo "❌ Not proceeded with update";
    exit 1
fi

echo -e "Stopping mirrorr..."
systemctl stop mirrorr-web

echo -e "Installing depenendencies..."

echo -e "Updating apt-get"
apt-get update

echo -e "Checking and installing RSync, Python and dependencies..."

#RSYNC
if command -v rsync >/dev/null 2>&1; then
    echo "RSync is installed. Awesome!"
else
    echo "RSync is not installed. Installing..."
    apt install rsync -y
fi

#PYTHON3
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION="$(python3 -V 2>&1 | cut -d' ' -f2)"
    if dpkg --compare-versions $PYTHON_VERSION lt 3.11; then
        echo "Required Python version is 3.11 or higher, please upgrade!"
        exit 1
    else
        echo "Python version $PYTHON_VERSION is installed. Awesome!"
    fi
else
    echo "Python 3 is not installed. Installing..."
    apt install python3 -y
fi

#PYTHON-FLASK
if python3 -c "import flask" &> /dev/null; then
    FLASK_VERSION="$(python3  -c 'import flask; print(flask.__version__)')"
    if dpkg --compare-versions $FLASK_VERSION lt 2.2.2; then
        echo "Required Python Flask version is 2.2.2 or higher, please upgrade!"
        exit 1
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
        exit 1
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
        exit 1
    else
        echo "Python Yaml version $YAML_VERSION is installed. Awesome!"
    fi
else
    echo "Python Yaml is not installed."
    apt install python3-yaml -y
fi

echo "Downloading..."
UPDATE_INSTALLATION_PATH="$INSTALLATION_PATH/__update"

mkdir -p "$UPDATE_INSTALLATION_PATH" || exit
cd "$UPDATE_INSTALLATION_PATH"

echo "Downloading..."
LATEST_TAG_URL="https://github.com/mchatzi/mirrorr/archive/refs/tags/$(wget -qLO - https://api.github.com/repos/mchatzi/mirrorr/releases/latest | grep tag_name | cut -d '"' -f 4).tar.gz"
wget -O main.tar.gz $LATEST_TAG_URL || { 
    echo "❌ Download failed"; exit 1; 
}

tar -xzf main.tar.gz || { echo "❌ Extraction failed"; exit 1; }
rm main.tar.gz

FOLDER_NAME=$(find . -mindepth 1 -maxdepth 1 -type d | head -n 1)
if [[ ! -d "$FOLDER_NAME" ]]; then
  echo "❌ Expected folder '$FOLDER_NAME' not found"
  exit 1
fi

mv ./$FOLDER_NAME/* .
rm -r ./$FOLDER_NAME

echo "Updating..."
rsync --archive --quiet --info=stats2 --no-owner --no-perms "$UPDATE_INSTALLATION_PATH/" "$INSTALLATION_PATH/"
cd "$INSTALLATION_PATH"
rm -r "$UPDATE_INSTALLATION_PATH"

chmod +x "$INSTALLATION_PATH/install.sh"
chmod +x "$INSTALLATION_PATH/update.sh"
chmod +x "$INSTALLATION_PATH/uninstall.sh"

echo "Application updated..."

while true; do
    read -p "Add mirrorr to group with access to shares (Enter to stop): " ALLOWED_GROUP
    [[ -z "$ALLOWED_GROUP" ]] && break

    if usermod -aG "$ALLOWED_GROUP" mirrorr; then
        echo "✔️ Added mirrorr to group: $ALLOWED_GROUP"
    else
        echo "❌ Failed to add mirrorr to group: $ALLOWED_GROUP"
    fi
done

if [ ! -d "$INSTALLATION_PATH/data/ssh" ]; then
    mkdir -p "$INSTALLATION_PATH/data/ssh"
fi

read -p "Create ssh public key for ssh connections? (y/N): " SETUP_SSH
if [ "$SETUP_SSH" == "y" ] || [ "$SETUP_SSH" == "y" ]; then
    echo "Setting up ssh key..."
    chmod 777 "$INSTALLATION_PATH/data/ssh"
    su -s /bin/sh mirrorr -c "ssh-keygen -N '' -t ed25519 -f '$INSTALLATION_PATH/data/ssh/id_ed25519' -C remote_to_mirrorr"
    echo "Pub key created: ($INSTALLATION_PATH/data/ssh/id_ed25519.pub). Copy this to remote ssh server:"
    cat "$INSTALLATION_PATH/data/ssh/id_ed25519.pub"

    read -p "Please enter remote server host (or ip) (Enter to cancel): " REMOTE_SSH_HOST
    if [[ -n "$REMOTE_SSH_HOST" ]]; then
        read -p "Please enter remote server port (Enter to cancel): " REMOTE_SSH_PORT
        if [[ -n "$REMOTE_SSH_PORT" ]]; then
            touch "$INSTALLATION_PATH/data/ssh/known_hosts"
            ssh-keygen -R "[$REMOTE_SSH_HOST]:$REMOTE_SSH_PORT" -f "$INSTALLATION_PATH/data/ssh/known_hosts"
            echo "Connecting to remote host to add to known_hosts..."
            ssh-keyscan -H -p "$REMOTE_SSH_PORT" "$REMOTE_SSH_HOST" >> "$INSTALLATION_PATH/data/ssh/known_hosts"
            chmod 400 "$INSTALLATION_PATH/data/ssh/known_hosts"
            echo "SSH was set up successfully!"
        fi
    fi    
fi
chmod 500 $INSTALLATION_PATH/data/ssh

#re-own everything
chown -R mirrorr:mirrorr "$INSTALLATION_PATH"

read -p "Start Mirrorr? (Y/n): " START_MIRRORR
if [ "$START_MIRRORR" != "N" ] && [ "$START_MIRRORR" != "n" ]; then
    echo "Starting application..."
    systemctl start mirrorr-web
fi

echo -e "\n✔️  Mirrorr has been updated!"

IP=$(ip a s dev eth0 | awk '/inet / {print $2}' | cut -d/ -f1)
echo -e "Web interface: $IP:5000"
