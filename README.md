# Mirrorr
Mirrorr is an orchestrator for rsync + systemd jobs. Plus a thin web frontend for managing all that. 
It supports configuring and scheduling (via systemd) rsync invocations.

Upon completion of an rsync job, logs are stored and made accessible via the web interface (and are also downloadable).
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
    ├── ssh/               # ssh connection keys and known_hosts
    ├── systemd/           # job systemd services will go here    
    └── conf.yaml          # mirrorr and mirrorr-web own config
├── sys/                   # mirrorr's main script + bash internals
└── web/                   # all web related files
    ├── frontend/          # FE files are here
    ├── logs/              # web app logs will go there
    ├── mirrorr_web.py     # main web app script
    └── .. more scripts    # more python scripts
├── install.sh             # installation script
├── update.sh              # update script
├── uninstall.sh           # uninstall script
└── requirements.txt       # python 
```

## Install

Mirrorr only runs on Linux (debian). See [System requirements](requirements.txt).

1. Run (as root), from any directory

    ```bash -c "$(wget -qLO - https://raw.githubusercontent.com/mchatzi/mirrorr/refs/heads/main/install.sh)"```
   
    (or download the sh and run it yourself). Mirrorr installs in ```/opt/mirrorr```.

    During installation you can specify user groups this user should belong to. See more for that [here](/docs/configuration.md#configuring-groups).  Additionally, you can set up the ssh connection for using remotes. See [here](/docs/configuration.md#configuring-remote-ssh-share).
   
    The installation installs rsync, python3, python3-flask, python3-yaml and python3-flask-cors, registers Mirrorr to run on startup and starts the Mirrorr web app.

2. Access the Frontend:
Open your browser and navigate to http://\<your-ip>:5000
(replace <your-ip> with the IP address of the machine running Mirrorr, as reported at the end of the installation).

## Configure
See [configuration](/docs/configuration.md)

## Use
* Create/edit file copy jobs across local and remote file shares
* View jobs, schedule them, enable/disable them. 'Running now' indication. Auto-refreshable homepage. Dry-run support.
* Import/export and copy jobs, import and export settings
* View and purge job logs. Auto log rotation built-in (10)
* Configurable threshold (percentage of deleted files in source), that aborts the job if exceeded
* Configurable [OpenObserve](https://openobserve.ai/) endpoint for receiving job reports
* Configurable [Discord webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) endpoint for receiving reports, configurable json template
* Heartbeat utility. Mirrorr sends a heartbeat every time a job runs, so you know it's up and running
* Rich set of rsync flags supported (configurable per job)
* Kill Job button. Asks systemctl to stop the user systemd (job) service. Do not do this when writing on filesystems that may get corrupted if writes suddenly get abandoned (e.g. exfat)
* Themes in the web interface

## Logs
To see logs for mirrorr web interface,```tail -f /opt/mirrorr/web/logs/mirrorr-web-be.log```.

To see job execution logs, first check the job logs in the web interface. Errors are reported there. Also see ```journalctl```. There you can also enable debug logs: 
a. per job, by setting 'Debug Job' to true in the job configuration (in the web interface) 
b. globally, by setting log level to debug in the mirrorr service unit (```/etc/systemd/system/mirrorr-web.service```). 

## Update
While the update.sh script is included in the installation directory, it may be outdated and thus it's recommended to run the latest version of it directly from the main branch: 

```bash -c "$(wget -qLO - https://raw.githubusercontent.com/mchatzi/mirrorr/refs/heads/main/update.sh)"```

If instead you choose to run the local script, ensure you don't run it from within mirrorr's installation directory (as that directory will be updated)

## Uninstall
Run uninstall.sh, or better fetch and run the latest version: 

```bash -c "$(wget -qLO - https://raw.githubusercontent.com/mchatzi/mirrorr/refs/heads/main/uninstall.sh)"```

Then follow on screen instructions. You have the option to save job data and config.

## Backups
Copy everything under /opt/mirrorr/data

There's also an export (and import) button in settings page in the web interface. And another export button per job, in the job details page. And another button, an import button, in the create new job page.

## Contributions
Take a look at the code, I kept things as simple as possible. No external libs. The code is meant to be:
- Dead simple, especially the FE
- Hopefully extremely fast
- Hoepfully ridiculously light on your machine and browser
- Fragile, I do very few validations and very few checks. Not sticking to only what the app does (eg by calling the mirrorr web api yourself) can definitely have unfortunate outcomes. Don't break the mirrorr!

Please contribute? See roadmap [here](https://github.com/mchatzi/mirrorr/issues/3)

## License
Mirrorr is licensed under the AGPL-3.0 license. For more details, see the [LICENSE](https://github.com/mchatzi/mirrorr/blob/main/LICENCE)  
  
Mirrorr web interface loads zero external scripts/css/fonts/imgs  
Support Open Source
