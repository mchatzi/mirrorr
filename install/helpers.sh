#!/bin/bash

# Check if the shell is using bash
ensure_bash() {
  if [[ "$(basename "$SHELL")" != "bash" ]]; then
    echo "You need a bash shell to run the installer"
    exit 2
  fi
}

# Run as root only
ensure_root() {
  if [[ "$(id -u)" -ne 0 || $(ps -o comm= -p $PPID) == "sudo" ]]; then
    echo "You need to be root or have sudo rights to run the installer"
    exit 2
  fi
}

# Check if systemd is running as the system init manager
ensure_systemd() {
  # Checks if PID 1 is systemd or if systemd-notify recognizes the system as booted
  if [[ "$(ps -p 1 -o comm=)" != "systemd" ]]; then
    echo "This installer requires a system powered by systemd"
    exit 2
  fi
}


prevent_runs_from_mirrorr_dir() {
    CURRENT_DIR="$(pwd)"
    case "$CURRENT_DIR/" in
        "$INSTALLATION_PATH/"* )
            echo -e "This directory or parent of, will be updated. Please execute update script from outside of $INSTALLATION_PATH or via the online source (bash -c \"$(wget -qLO - wget -qLO - https://raw.githubusercontent.com/mchatzi/mirrorr/refs/heads/main/update.sh)\")"
            exit 2
            ;;
    esac
}


do_rsync_and_python_deps() {
  echo -e "Checking and installing RSync, Python and dependencies..."

  #RSYNC
  if command -v rsync >/dev/null 2>&1; then
      echo "RSync is installed. Awesome!"
  else
      read -p "RSync is not installed. Mirrorr depends on rsync. Install? (Y,n): " INSTALL_RSYNC
      if [ "$INSTALL_RSYNC" = "N" ] || [ "$INSTALL_RSYNC" = "n" ]; then
          echo "Rsync not installed, installation aborted"
          exit 2
      else
          apt-get update
          apt install rsync -y
      fi
  fi

  #PYTHON3
  if command -v python3 >/dev/null 2>&1; then
      PYTHON_VERSION="$(python3 -V 2>&1 | cut -d' ' -f2)"
      if dpkg --compare-versions $PYTHON_VERSION lt 3.11; then
          echo "Required Python version is 3.11 or higher, please upgrade!"
          exit 2
      else
          echo "Python version $PYTHON_VERSION is installed. Awesome!"
      fi
  else
      read -p "Python 3 is not installed. Mirrorr depends on python. Install? (Y,n): " INSTALL_PYTHON
      if [ "$INSTALL_PYTHON" = "N" ] || [ "$INSTALL_PYTHON" = "n" ]; then
          echo "Python not installed, installation aborted"
          exit 2
      else
          apt-get update
          apt install python3 -y
      fi
  fi

  #PYTHON3-VENV
  if python3 -c "import venv, ensurepip" &> /dev/null; then
    echo "Python3 venv is installed. Awesome!"
  else
    read -p "Python3 venv is not installed. Mirrorr depends on this. Install? (Y,n): " INSTALL_VENV
    if [ "$INSTALL_VENV" = "N" ] || [ "$INSTALL_VENV" = "n" ]; then
        echo "Python3 venv not installed, installation aborted"
        exit 2
    else
        apt-get update
        apt install python3-venv -y
    fi
  fi
}


do_pip_deps() {
  echo "Installing python environment"

  python3 -m venv "$INSTALLATION_PATH/app/web/.venv"
  "$INSTALLATION_PATH/app/web/.venv/bin/pip" install -r "$INSTALLATION_PATH/install/requirements-web.txt"

  python3 -m venv "$INSTALLATION_PATH/app/sys/.venv"
  "$INSTALLATION_PATH/app/sys/.venv/bin/pip" install -r "$INSTALLATION_PATH/install/requirements-mirrorr.txt"

}

do_user_and_groups() {
  if [ $IS_UPDATE = 0 ]; then
      echo "Creating user and group (mirrorr:mirrorr)..."
      groupadd --system mirrorr
      adduser --system \
        --disabled-login \
        --shell /bin/false \
        --ingroup mirrorr \
        --home "$INSTALLATION_PATH/data" \
        mirrorr
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
}


do_ssh() {
  if [ ! -d "$INSTALLATION_PATH/data/ssh" ]; then
    mkdir -p "$INSTALLATION_PATH/data/ssh"
  fi

  read -p "Create ssh public key for ssh connections? (y/N): " SETUP_SSH
  if [ "$SETUP_SSH" = "y" ] || [ "$SETUP_SSH" = "y" ]; then
      echo "Setting up ssh key..."
      chmod 777 "$INSTALLATION_PATH/data/ssh"
      su -s /bin/sh mirrorr -c "ssh-keygen -N '' -t ed25519 -f '$INSTALLATION_PATH/data/ssh/id_ed25519' -C remote_to_mirrorr"
      echo "Pub key created: ($INSTALLATION_PATH/data/ssh/id_ed25519.pub)"
      echo "❗️ Copy the content of this file to remote ssh server before proceeding ❗️"
      echo "Content:"
      cat "$INSTALLATION_PATH/data/ssh/id_ed25519.pub"

      read -p "Please enter remote server host (or ip) (Enter to cancel): " REMOTE_SSH_HOST
      if [ -n "$REMOTE_SSH_HOST" ]; then
          read -p "Please enter remote server port (Enter to cancel): " REMOTE_SSH_PORT
          if [ -n "$REMOTE_SSH_PORT" ]; then
              KNOWN_HOSTS_FILE="$INSTALLATION_PATH/data/ssh/known_hosts"

              if [ $IS_UPDATE = 1 ]; then
                  echo "Removing any old entries from known_hosts"
                  touch "$KNOWN_HOSTS_FILE"
                  # Remove all entries for this host and port
                  ssh-keygen -R "[$REMOTE_SSH_HOST]:$REMOTE_SSH_PORT" -f "$KNOWN_HOSTS_FILE"
              fi

              echo "Connecting to remote host to add to known_hosts..."
              ssh-keyscan -H -p "$REMOTE_SSH_PORT" "$REMOTE_SSH_HOST" >> "$KNOWN_HOSTS_FILE"
              chmod 400 "$KNOWN_HOSTS_FILE"

              #Set ssh port in mirrorr's conf.yaml
              CONFIG_FILE="$INSTALLATION_PATH/data/conf.yaml"
              if [ ! -f $CONFIG_FILE ]; then
                  printf "remote_ssh_port: %s\n" "$REMOTE_SSH_PORT" > "$CONFIG_FILE"
              else
                  if grep -q "^remote_ssh_port:" "$CONFIG_FILE"; then
                      sed -i "s|^remote_ssh_port:.*|remote_ssh_port: ${REMOTE_SSH_PORT}|" "$CONFIG_FILE"
                  else
                      printf "remote_ssh_port: %s\n" "$REMOTE_SSH_PORT" >> "$CONFIG_FILE"
                  fi
              fi
              echo "SSH was set up successfully!"
          fi
      fi
  fi

  chmod 500 "$INSTALLATION_PATH/data/ssh"
}


register_mirror_service_on_startup() {
  echo "Registering service.."
  local EXEC_START="\"$INSTALLATION_PATH/app/web/.venv/bin/gunicorn\" \
--bind 0.0.0.0:5000 \
--workers 1 \
--threads 4 \
--log-level info \
mirrorr_web:app"

  local WORKING_DIRECTORY="$INSTALLATION_PATH/app/web"

  cat > "/etc/systemd/system/mirrorr-web.service" <<EOL
[Unit]
Description=Run mirrorr-web on startup
After=network.target
[Service]
Type=simple
ExecStart=$EXEC_START
WorkingDirectory=$WORKING_DIRECTORY
User=mirrorr
Group=mirrorr
[Install]
WantedBy=multi-user.target
EOL

  systemctl daemon-reload
  systemctl enable mirrorr-web
}


run_updaters() {
  echo "Checking if any updaters must run..."
  local file
  local filename

  for file in "$BASE_DOWNLOADED_DIR"/install/updaters/*; do
    # Ensure it's a file and extract just the filename from the path
    [ -f "$file" ] || {
      echo "Error while running updater. Updater file not found! Update aborted or your mirrorr is partially upgraded. Before re-attempting, please check what version you are now at (check your .version file)"
      exit 2
    }

    filename=$(basename "$file")
    UPDATER_VERSION="$(echo "$filename" | sed 's/^v//; s/-updater\.sh$//')"

    #Updater must run if the installation is on an older version than this updater is meant for and 
    # only if the updater is not for a later version than the version we're installing.
    # We rely that the loop we're in is giving us the updaters sorted by version
    if dpkg --compare-versions $INSTALLED_VERSION lt $UPDATER_VERSION &&
        dpkg --compare-versions $UPDATER_VERSION le $VERSION_TO_INSTALL; then
      chmod +x "$file"
      source "$file"
    fi
  done
}