#!/bin/bash

echo "This updater will update your Mirrorr to v0.6.0-alpha"

convert_settings_to_integers() {
    "$INSTALLATION_PATH/app/web/.venv/bin/python" -c "
import yaml

conf_file_path = '$INSTALLATION_PATH/data/conf.yaml'
settings = {}

with open(conf_file_path, 'r') as f:
    settings = yaml.safe_load(f) or {}

for field in ['scheduler_cycle_s', 'ui_refresher_s', 'log_retention_count', 'remote_ssh_port']:
    if field in settings and settings[field] is not None:
        settings[field] = int(settings[field])
        print(f'Converted field {field} to integer')

with open(conf_file_path, 'w') as f:
    yaml.dump(settings, stream=f, sort_keys=False)
"
}

convert_settings_to_integers
echo "✔️  Updater v0.6.0-alpha run successfully"







