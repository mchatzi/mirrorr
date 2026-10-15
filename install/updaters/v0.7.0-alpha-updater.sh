#!/bin/bash

echo "This updater will update your Mirrorr to v0.7.0-alpha"

convert_jobs() {
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
                job['wrap_with_nice'] = job['rsync_nice']
                job.pop('rsync_nice')
                print(f'Renamed field rsync_nice')
            
            if 'rsync_ionice' in job and job['rsync_ionice'] is not None:
                job['wrap_with_ionice'] = job['rsync_ionice']
                job.pop('rsync_ionice', None)
                print(f'Renamed field rsync_ionice')

            enabled_reporters = ''
            if 'reporter_discord' in job:
                if job['reporter_discord'] is True:
                    enabled_reporters += 'Discord'
                job.pop('reporter_discord', None)

            if 'reporter_o2' in job:
                if job['reporter_o2'] is True:
                    enabled_reporters += (',' if enabled_reporters else '') + 'OpenObserve'
                job.pop('reporter_o2', None)

            job['enabled_reporters'] = enabled_reporters

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

    #health_heartbeat_url became nested
    if 'health_heartbeat_url' in settings:
        settings['heartbeat'] = {
            'endpoint': settings.get('health_heartbeat_url') or ''
            'method': 'GET'
        }
        settings.pop('health_heartbeat_url', None)
    
    #value 600 for scheduler_cycle_s removed
    if 'scheduler_cycle_s' in settings:
        if settings['scheduler_cycle_s'] == 600:
            settings['scheduler_cycle_s'] = 60
    
    #your_brand renamed to environment
    if 'your_brand' in settings:
        settings['environment'] = settings['your_brand'] or ''
        settings.pop('your_brand', None)

    #log_retention_count moved to job yaml
    if 'log_retention_count' in settings:
        settings.pop('log_retention_count', None)

    #o2_reporter becomes a reporter under the new reporters array
    if 'o2_reporter' in settings and settings['o2_reporter'].get('o2_server_url'):
        if not 'reporters' in settings:
            settings['reporters'] = []

        settings['reporters'].append({
            'name': 'OpenObserve',
            'endpoint': settings['o2_reporter'].get('o2_server_url'),
            'headers': 'Authorization: Basic ' + (settings['o2_reporter'].get('o2_server_auth') or ''),
            'method': 'POST' 
        })
        settings.pop('o2_reporter', None)
    
    #discord_reporter becomes a reporter under the new reporters array
    if 'discord_reporter' in settings and settings['discord_reporter'].get('webhook_url'):
        if not 'reporters' in settings:
            settings['reporters'] = []

        settings['reporters'].append({
            'name': 'Discord',
            'endpoint': settings['discord_reporter'].get('webhook_url'),
            'method': 'POST',
            'template': settings['discord_reporter'].get('template') or ''
        })
        settings.pop('discord_reporter', None)

    with open(conf_file_path, 'w') as f:
        yaml.dump(settings, stream=f, sort_keys=False)
except Exception as e:
    print('Error while updating settings')

print('Converted settings')
"
}

convert_jobs
convert_settings

echo "✔️  Updater v0.7.0-alpha has run"