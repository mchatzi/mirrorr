#!/bin/bash

echo "This updater will update your Mirrorr to v0.5.0-alpha"

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
