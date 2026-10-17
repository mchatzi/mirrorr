#!/bin/bash
set -e

INSTALLATION_PATH="/opt/mirrorr"
CREDS_FILE="$INSTALLATION_PATH/data/.creds"

source "$INSTALLATION_PATH/install/helpers.sh"

MIRRORR_LOGIN_USERNAME="${MIRRORR_LOGIN_USERNAME:-admin}"
MIRRORR_LOGIN_PASSWORD="${MIRRORR_LOGIN_PASSWORD:-password}"
MIRRORR_ENABLE_SUDO="${MIRRORR_ENABLE_SUDO:-false}"

# Setup Credentials
echo "Setting Mirrorr login credentials..."

mkdir -p "$INSTALLATION_PATH/data"

"$INSTALLATION_PATH/app/web/.venv/bin/python" - "$CREDS_FILE" "$MIRRORR_LOGIN_USERNAME" "$MIRRORR_LOGIN_PASSWORD" <<'EOF'
import sys
from werkzeug.security import generate_password_hash

filename, username, password = sys.argv[1:]

with open(filename, "w") as f:
    f.write(username + " ")
    f.write(generate_password_hash(password))
    f.write("\n")
EOF

chmod 400 "$CREDS_FILE"
chown mirrorr:mirrorr "$CREDS_FILE"


# Setup Sudo
if [ "$MIRRORR_ENABLE_SUDO" = "true" ]; then
    do_sudoers
else
    undo_sudoers
fi



# Updaters
DATA_VERSION_FILE="$INSTALLATION_PATH/data/.version"
VERSION_TO_INSTALL=$(<"$INSTALLATION_PATH/install/.version")

if [ -f "$DATA_VERSION_FILE" ]; then
    INSTALLED_VERSION=$(<"$DATA_VERSION_FILE")

    if dpkg --compare-versions "$VERSION_TO_INSTALL" lt "$INSTALLED_VERSION"; then
        echo "❌  You are trying to install an older version! Current version is $INSTALLED_VERSION"
        exit 2
    fi

    echo "Running Updaters..."
    run_updaters \
        "$INSTALLATION_PATH/install/updaters" \
        "$INSTALLED_VERSION" \
        "$VERSION_TO_INSTALL"
fi

# Record the version whose updaters have completed successfully.
echo "$VERSION_TO_INSTALL" > "$DATA_VERSION_FILE"
chown mirrorr:mirrorr "$DATA_VERSION_FILE"



echo "Starting Mirrorr..."

# Add usergroups Mirrorr
if [ -n "$MIRRORR_USERGROUPS" ]; then
    IFS=',' read -ra GIDS <<< "$MIRRORR_USERGROUPS"
    for gid in "${GIDS[@]}"; do
        if ! getent group "$gid" >/dev/null; then
            groupadd --gid "$gid" "mapped-group-$gid"
        fi
        group_name=$(getent group "$gid" | cut -d: -f1)
        usermod -aG "$group_name" mirrorr
    done
fi

exec runuser -u mirrorr -- "$@"
