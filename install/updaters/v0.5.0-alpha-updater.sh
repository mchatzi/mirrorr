#!/bin/bash

echo "This updater will update your Mirrorr to v0.5.0-alpha"

clean_up_js_mess() {
    MESSY_FOLDER="$INSTALLATION_PATH/app/web/frontend"
    for forgotten_file in "index.js" "job.js" "joblog.js" "settings.js"; do
        if [ -f "$MESSY_FOLDER/$forgotten_file" ]; then
            echo "removing leftover: $MESSY_FOLDER/$forgotten_file"
            rm -f "$MESSY_FOLDER/$forgotten_file";
        fi    
    done
}

clean_up_js_mess

register_gunicorn_systemd() {
    echo "Unregistering flask-based mirrorr service..."
    systemctl stop mirrorr-web
    systemctl disable mirrorr-web.service
    rm /etc/systemd/system/mirrorr-web.service
    systemctl daemon-reload

    echo "Replacing with the gunicorn-based systemd service..."
    register_mirror_service_on_startup

}

register_gunicorn_systemd
