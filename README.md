# Mirrorr

Mirrorr is an orchestrator for rsync + systemd jobs. Plus a thin web frontend for managing all that. 
It supports configuring and scheduling (via systemd) rsync invocations.

Upon completion of an rsync job, logs are stored and made accessible via the web interface (and also downloadable).
A job report is generated (json) and can be sent to [OpenObserve](https://openobserve.ai/) servers, and as a notification to [Discord webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks).

## Why
Because I couldn't find a file sync application that supports deleting files on the destination but at the same time support **aborting** the sync if a big (configurable) 
percentage of files have been **deleted** in the source directory. This guards from accidental 
deletions in your backup (the destination) in case your source was hacked/accidentally emptied.

## Screenshots
See [screenshots](/screenshots/screenshots.md)

## What
 The parts that make up Mirrorr are:

- **rsync invocation engine:** executes rsync, with parameters loaded from your job configuration
- **systemd management:** mirrorr executes systemctl commands to enable/disable jobs and bash scripts for registering/removing timers with systemd
- **web app:** a simple web interface for managing everything

#### Folder Structure (after installation)

```plaintext
mirrorr
└── data                   # Runtime generated folder
    ├── jobs/              # job configurations will go here 
    ├── logs/              # job logs will go there
    ├── systemd/           # job systemd services will go here    
    └── conf.yaml          # mirrorr and mirrorr-web own config
├── sys/                   # mirrorr's main script + bash internals
└── web/                   # all web related files
    ├── frontend/          # FE files are here
    ├── logs/              # eeb app logs will go there
    └── mirrorr-web.py     # main web app script
├── install.sh             # installation script, not really, we'll see
└── requirements.txt       # python 
```

## Install

#### Mirrorr only runs on Linux

1. Run (as root), from anywhere, ```bash -c "$(wget -qLO - https://github.com/mchatzi/mirrorr/install-mirrorr.sh)"``` (or download the sh and run it yourself)

   Mirrorr installs in ```/opt/mirrorr```. During installation you can specify user groups this user should belong to. Specify the groups that have access to the shares you want to run mirrorr on.
   
   The installation installs rsync, python3, python3-flask, python3-yaml and python3-flask-cors, registers Mirrorr to run on startup and starts the Mirrorr web app

1. Access the Frontend:
   
    Open your browser and navigate to http://\<your-ip>:5000
   
    (replace <your-ip> with the IP address of the machine running Mirrorr, as reported at the end of the installation).

## Uninstall

Is a bit manual atm..

1. Delete all your jobs
1. Unregister mirrorr from startup. Run:
   1. ```systemctl disable mirrorr-web```
   1. ```rm /etc/systemd/system/mirrorr-web.service```
1. Remove directory /opt/mirrorr

## Configure
See [configuration](/docs/configuration.md)

## Use

* View jobs, option to enable/disable a job, option to auto-refreshing the page. 'Running now' indication
* Create/edit jobs with validations for all fields. ```Schedule``` expects the format used in systemd's timer's ```OnCalendar``` entries. ```Source``` and ```Dest``` must be absolute paths, and they are checked for existence when creating/updating a job. Newly created jobs are initially disabled.
* Schedule timers in user scope. Lingering services.
* View and purge job logs. Auto log rotation built-in (10)
* Configurable threshold (percentage of deleted files in source), that aborts the job if exceeded
* Configurable [OpenObserve](https://openobserve.ai/) endpoint for receiving job reports
* Configurable [Discord webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) endpoint for receiving reports, configurable json template
* Heartbeat utility. Requires a receiving server that supports push notifications (e.g. [Uptime Kuma](https://uptimekuma.org/)). Mirrorr sends a heartbeat every time a job runs, so you know it's up and running
* Detailed rsync configuration per job
* Kill Job button. Asks systemctl to stop the user systemd service. Do not do this when writing on filesystems that may get corrupted if writes suddenly get abandoned (e.g. exfat)
* Themes in the web interface


## Backups
Copy everything under /opt/mirrorr/data

There's also an export (and import) button in settings page in the web interface. And another export button per job, in the job details page. And another button, an import button, in the create new job page.

## Contributions
Take a look at the code, I kept things as simple as possible. I didn't see the reason for using overbloated libs.. the code is:
- Dead simple, especially the FE
- Not buggy, there's not much code to get buggy..
- Stupidously fast
- Ridiculously light on your machine and browser
- Fragile, I do very few validations and very few checks. Not sticking to what the app does (eg by calling the mirrorr web api yourself) can definitely have unfortunate outcomes. Don't break the mirrorr!
  
To see logs for mirrorr, tail ```/opt/mirrorr/web/logs/mirrorr-web-be.log```.

To see more logs, set log level to debug, in the mirrorr service unit (```/etc/systemd/system/mirrorr-web.service```). Also check journalctl as it may also contain systemd logs.

Please do fork, make PRs, file issues...

## TODO

- Dockerization:
Create Docker containers (or a Docker Compose configuration)

- Support Shoutrrr

## License
Mirrorr is licensed under the AGPL-3.0 license. For more details, see the [LICENSE](https://github.com/mchatzi/mirrorr/blob/main/LICENCE)  
  
Mirrorr web interface loads zero external scripts/css/fonts/imgs  
Support Open Source

