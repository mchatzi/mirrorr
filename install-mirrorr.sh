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

echo -e "Updating apt-get"
apt-get update

echo -e "Checking and installing Python and dependencies..."

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

echo "Installing application..."
read -p "Installation path (press enter for /opt/mirrorr) " INSTALLATION_PATH
if [ -n "$INSTALLATION_PATH" ]; then
    echo -e "Installing at $INSTALLATION_PATH"
else
    INSTALLATION_PATH="/opt/mirrorr"
    echo -e "Installing at $INSTALLATION_PATH"
fi

mkdir -p "$INSTALLATION_PATH"
cd "$INSTALLATION_PATH"
wget -qO main.tar.gz https://api.github.com/repos/mchatzi/mirrorr/tarball --header 'Authorization: token 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'
tar -xzf main.tar.gz
rm main.tar.gz
FOLDER_NAME="$(ls)"
mv $FOLDER_NAME/* .
rm -r $FOLDER_NAME

echo "Registering to run on startup"

command_with_quotes="python3 \"$INSTALLATION_PATH/web/mirrorr-web.py\" --log=WARNING"
shell_ready_command=$(bash -c "printf '%q ' $command_with_quotes")
COMMAND_FOR_EXECSTART=$(echo ${shell_ready_command} | sed 's/\\/\\\\/g')

shell_ready_working_dir=$(bash -c "printf '%q ' \"$INSTALLATION_PATH\"")
WORKING_DIRECTORY=$(echo ${shell_ready_working_dir} | sed 's/\\/\\\\/g')

cat > "/etc/systemd/system/mirrorr-web.service" <<EOL
[Unit]
Description=Run mirrorr-web on startup
After=network.target
[Service]
Type=simple
ExecStart=bash -c "$COMMAND_FOR_EXECSTART"
WorkingDirectory=$WORKING_DIRECTORY
[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reexec
systemctl daemon-reload
systemctl enable mirrorr-web

echo "Starting application..."
systemctl start mirror-web

#Report to user
IP=$(ip a s dev eth0 | awk '/inet / {print $2}' | cut -d/ -f1)
echo -e "Mirrorr is up and running!"
echo -e "Web interface: $IP:5000"
