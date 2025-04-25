# Mirrorr

Mirrorr is an orchestrator for rsync + systemd jobs. Plus a thin web frontend for managing all that. 
It supports configuring and scheduling (via systemd) rsync invocations.

Upon completion of an rsync job, logs are stored and made accessible via the web interface (and also downloadable).
A job report is generated (json) and can be sent to OpenObserve servers, and as a notification to Discord webhooks.

## Why
Because I couldn't find a sync application that supports deleting files on the destination
(a true mirror) but at the same time support **aborting** the sync if a big (configurable) 
percentage of files were found to have been **deleted** in the source directory. This guards from accidental 
deletions in your backup (the destination) in case your source was hacked/accidentally emptied.

## What
 The parts that make up Mirrorr are:

- **rsync invocation engine:** executes rsync, with parameters loaded from your job configuration
- **systemd management:** mirrorr executes systemctl commands to enable/disable jobs and bash scripts for registering/removing timers with systemd
- **web app:** a simple web interface for managing your jobs

#### Folder Structure (after installation)

```plaintext
mirrorr
└── data                   # Runtime generated folder
    ├── jobs/              # job configurations will go here 
    ├── logs/              # job logs will go there
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

1. Clone the Repository:
    ```
    git clone <repository-url>
    cd mirrorr
    ```
1. Install Python Dependencies (optionally in Virtual Environment):
    ```
    apt install python3-flask
    apt install python3-yaml
    apt install python3-flask-cors
    ```
1. Run the Mirrorr web app:
    ```
    [setsid] python3 web/mirrorr-web.py --log WARNING
    ```
   Normally you'd want to run Mirrorr with ```setsid``` and have it start on startup

1. Access the Frontend:
   
    Open your browser and navigate to http://\<your-ip>:5000
   
    (replace <your-ip> with the IP address of the machine running Mirrorr).

## Use

* View jobs, option to enable/disable a job, option to auto-refreshing the page. 'Running now' indication
* Create/edit jobs with validations for all fields. ```Schedule``` expects the format used in systemd's timer's ```OnCalendar``` entries. ```Source``` and ```Dest``` must be absolute paths, and they are checked for existence when creating/updating a job
* Schedule timers in either system or user scope. Persistent=true by default. Type=oneshot by default
* View and purge job logs. Auto log rotation built-in (10)
* Configurable threshold (percentage of deleted files in source), that aborts the job if exceeded
* Configurable OpenObserve endpoint for receiving job reports
* Configurable Discord webhook endpoint for receiving reports, configurable json template
* Heartbeat utility. Requires a receiving server that supports push notifications (e.g. Uptime Kuma). Mirrorr send a heartbeat every time a job runs, so you know your it's up and running
* Themes in the web interface

#### Example schedules:
* Every 20 minutes: ```*:0/20```
* Every hour: ```*-*-* *:00:00``` or ```hourly```
* Every 2 hours: ```0/2:00:00```
* Every day at 4:30 AM: ```*-*-* 4:30:00```
* Every first of the month at midnight: ```*-*-01 00:00:00```
* Every Monday at 10 PM:```Mon *-*-* 22:00:00```

## TODO
- Dockerization:
Create Docker containers (or a Docker Compose configuration) for easy deployment.

## License
MIT License

