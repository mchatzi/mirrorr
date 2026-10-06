#!/bin/bash

echo "This updater will update your Mirrorr to v0.7.0-alpha"

rename_nice_and_ionice_job_attributes() {
    "$INSTALLATION_PATH/app/web/.venv/bin/python" -c "
import yaml
from pathlib import Path

JOBS_DIR_PATH = '$INSTALLATION_PATH/data/jobs'
jobs_dir = Path(JOBS_DIR_PATH)
for file in jobs_dir.iterdir():
    if file.name.endswith('.yaml'):
        try:
            job = {}
            with open(Path(JOBS_DIR_PATH) / file.name, 'r') as f:
                job = yaml.safe_load(f)

                if 'rsync_nice' in job and job['rsync_nice'] is not None:
                    try:
                        job['wrap_with_nice'] = job['rsync_nice']
                        job.pop('rsync_nice')
                        print(f'Renamed field rsync_nice')
                    except Exception as ee:
                        print(f'Error renaming rsync_nice')
                
                if 'rsync_ionice' in job and job['rsync_ionice'] is not None:
                    try:
                        job['wrap_with_ionice'] = job['rsync_ionice']
                        job.pop('rsync_ionice', None)
                        print(f'Renamed field rsync_ionice')
                    except Exception as ee:
                        print(f'Error renaming rsync_ionice')

            with open(Path(JOBS_DIR_PATH) / file.name, 'w') as f:
                yaml.dump(job, stream=f, sort_keys=False)
        except Exception as e:
            print(f'Error while updating {file.name}')
"
}

convert_settings() {
    "$INSTALLATION_PATH/app/web/.venv/bin/python" -c "
import yaml

conf_file_path = '$INSTALLATION_PATH/data/conf.yaml'
settings = {}

try:
    with open(conf_file_path, 'r') as f:
        settings = yaml.safe_load(f) or {}

    if 'health_heartbeat_url' in settings:
        settings['heartbeat'] = {
            'health_heartbeat_url': settings.get('health_heartbeat_url', '')
        }
        settings.pop('health_heartbeat_url', None)
    
    if 'scheduler_cycle_s' in settings:
        if settings['scheduler_cycle_s'] == 600:
            settings['scheduler_cycle_s'] = 60
    
    if 'your_brand' in settings:
        settings['environment'] = settings['your_brand']
        settings.pop('your_brand', None)

    if 'log_retention_count' in settings:
        settings.pop('log_retention_count', None)
    
    with open(conf_file_path, 'w') as f:
        yaml.dump(settings, stream=f, sort_keys=False)
except Exception as e:
    print('Error while updating settings')

print('Converted settings')
"
}

convert_settings
rename_nice_and_ionice_job_attributes

echo "✔️  Updater v0.7.0-alpha has ran"