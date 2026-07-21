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

ensure_bash
ensure_root

echo -e "Loading..."

INSTALLATION_PATH="/opt/mirrorr"

if [ -d "$INSTALLATION_PATH" ]; then
    echo -e "❌ Installation found at $INSTALLATION_PATH. Are you trying to update? Run updater script"
    exit 1
fi

read -p "This will install Mirrorr. Continue? (Y/n): " DO_INSTALL
if [ "$DO_INSTALL" == "N" ] || [ "$DO_INSTALL" == "n" ]; then
    echo "❌ Not proceeded with installing"
    exit 1
fi

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

mkdir -p "$INSTALLATION_PATH"
cd "$INSTALLATION_PATH"

echo "Downloading application..."
wget -O main.tar.gz https://api.github.com/repos/mchatzi/mirrorr/tarball || 
    { echo "❌ Download failed"; exit 1; }

tar -xzf main.tar.gz || { echo "❌ Extraction failed"; exit 1; }
rm main.tar.gz

FOLDER_NAME=$(find . -mindepth 1 -maxdepth 1 -type d | head -n 1)
if [[ ! -d "$FOLDER_NAME" ]]; then
  echo "❌ Expected folder '$FOLDER_NAME' not found"
  exit 1
fi

echo "Installing..."
mv ./$FOLDER_NAME/* .
rm -r ./$FOLDER_NAME

chmod +x "$INSTALLATION_PATH/install-mirrorr.sh"
chmod +x "$INSTALLATION_PATH/update-mirrorr.sh"
chmod +x "$INSTALLATION_PATH/uninstall.sh"

echo "Creating user and group (mirrorr:mirrorr)..."
groupadd --system mirrorr
adduser --system --disabled-login --shell /bin/false --ingroup mirrorr --home $INSTALLATION_PATH/data/systemd mirrorr

while true; do
    read -p "Add mirrorr to group with access to shares (Enter to stop): " ALLOWED_GROUP
    [[ -z "$ALLOWED_GROUP" ]] && break

    if usermod -aG "$ALLOWED_GROUP" mirrorr; then
        echo "✔️ Added mirrorr to group: $ALLOWED_GROUP"
    else
        echo "❌ Failed to add mirrorr to group: $ALLOWED_GROUP"
    fi
done

#Ensure systemd services from this user linger
loginctl enable-linger mirrorr
mkdir -p "$INSTALLATION_PATH/data/systemd/.config/systemd/user"

mkdir -p "$INSTALLATION_PATH/data/ssh"

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
            echo "Connecting to remote host to add to known_hosts..."
            ssh-keyscan -H -p "$REMOTE_SSH_PORT" "$REMOTE_SSH_HOST" >> "$INSTALLATION_PATH/data/ssh/known_hosts"
            chmod 400 "$INSTALLATION_PATH/data/ssh/known_hosts"
            echo "SSH was set up successfully!"
        fi
    fi    
fi

chmod 500 "$INSTALLATION_PATH/data/ssh"

#own everything
chown -R mirrorr:mirrorr "$INSTALLATION_PATH"

echo "Registering service.."
command_with_quotes="python3 \"$INSTALLATION_PATH/web/mirrorr_web.py\" --log=WARNING"
shell_ready_command=$(bash -c "printf '%q ' $command_with_quotes")
COMMAND_FOR_EXECSTART=$(echo ${shell_ready_command} | sed 's/\\/\\\\/g')

WORKING_DIRECTORY=$(echo ${INSTALLATION_PATH} | sed 's/\\//g')

cat > "/etc/systemd/system/mirrorr-web.service" <<EOL
[Unit]
Description=Run mirrorr-web on startup
After=network.target
[Service]
Type=simple
ExecStart=bash -c "$COMMAND_FOR_EXECSTART"
WorkingDirectory=$WORKING_DIRECTORY
User=mirrorr
Group=mirrorr
[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reexec
systemctl daemon-reload
systemctl enable mirrorr-web

read -p "Start Mirrorr? (Y/n): " START_MIRRORR
if [ "$START_MIRRORR" != "N" ] && [ "$START_MIRRORR" != "n" ]; then
    echo "Starting application..."
    systemctl start mirrorr-web

    echo -e "\n✔️ Mirrorr is up and running! Installed at $INSTALLATION_PATH."
else
    echo -e "\n✔️ Mirrorr has been nstalled at $INSTALLATION_PATH. Start with systemctl 'start mirrorr-web'"
fi

IP=$(ip a s dev eth0 | awk '/inet / {print $2}' | cut -d/ -f1)
echo -e "Web interface: $IP:5000"
