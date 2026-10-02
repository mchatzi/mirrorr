# Mirrorr
Mirrorr is an orchestrator for rsync jobs. Plus a thin web frontend for managing all that. 
It supports configuring and scheduling rsync invocations.

Upon completion of an rsync job, logs are stored and made accessible via the web interface (and are also downloadable).
A job report is generated (json) and can be sent to [OpenObserve](https://openobserve.ai/) servers, and as a notification to [Discord webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks).

## Screenshots
See [screenshots](/screenshots/screenshots.md)

## Get started

### Bare-bones/Linux Containers install 
  To get the latest version, run (as root), and from any directory:
```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/mchatzi/mirrorr/refs/heads/main/install/install-latest.sh)"
```
Check the [installation](/docs/install.md) guide for more information

## What
The parts that make up Mirrorr are:

- **rsync invocation engine:** executes rsync, with parameters loaded from your job configuration, notifies through your reporters
- **job scheduler:** mirrorr uses internal scheduler to run jobs enable/disable jobs, supporting queuing and restart after server reboots
- **web app:** a simple web interface for managing everything

#### Folder Structure (after installation)

```plaintext
mirrorr
└── data                    # Runtime generated folder
    ├── jobs/               # job configurations will go here 
    ├── logs/               # job logs will go there
    ├── ssh/                # ssh connection keys and known_hosts
    └── conf.yaml           # mirrorr and mirrorr-web own config
├── install/                # installers
├── docs/                   # readme etc
└── app/                    # mirrorr app
    ├── sys/                # job execution engine
    └── web/                # all web related files
        ├── frontend/       # FE files are here
        ├── logs/           # app logs go here
        ├── mirrorr_web.py  # main web app script
        └── ..more scripts  # more python scripts
```

## Why
Because I couldn't find a file sync application that supports deleting files on the destination but at the same time support **aborting** the sync if a big (configurable) 
percentage of files have been **deleted** in the source directory. This guards from accidental 
deletions in your backup (the destination) in case your source was hacked/accidentally emptied.

## How
* Backup files and folders, local or remotely, fast (delta)
* Share files - setup shared remote folders
* Create/edit/view/schedule/import/export/copy/run/kill file mirror jobs across local and remote file shares
* Dry-run support. Configurable threshold (percentage of deleted files in source), that aborts the job if exceeded 
* Configurable reporting with [OpenObserve](https://openobserve.ai/) and [Discord webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) 
* Heartbeat utility. Mirrorr sends a heartbeat every time a job runs, so you know it's up and running
* Rich set of rsync flags supported (configurable per job)

See [configuration](/docs/configuration.md) and [job configuration](/docs/job%20configuration.md).

## Logs
Mirrorr keeps by default a history of all logs for each job it runs. These are accessible and downloadable via the web interface. For configuring logging, and other advanced logging topics, see [logs](/docs/setup.md#logs).

## Backups
To make a backup of all your jobs and configuration, simply copy everything under `/opt/mirrorr/data` (with for example a mirrorr job). All runtime data is stored there and this directory is not touched during updates.

There are also export and import buttons: in settings page, to export/import settings, in the job configuration page, to export/import jobs and in the job log page for downloading job logs.

## Contributions
I kept the code as simple as possible. No external libs. Back to basics. The code is:
- Dead simple, especially the FE
- Hopefully extremely fast
- Hopefully ridiculously light on your machine and browser
- Somewhat fragile, this is not an app secured against bad users. Not sticking to only what the app does (eg by calling the mirrorr web api yourself) can definitely have unfortunate outcomes. Don't break the mirrorr!

Please contribute? See roadmap [here](https://github.com/mchatzi/mirrorr/issues/3)

## License
Mirrorr is licensed under the AGPL-3.0 license. For more details, see the [LICENSE](https://github.com/mchatzi/mirrorr/blob/main/LICENCE)  
  
Mirrorr web interface loads zero external scripts/css/fonts/imgs. Some fonts/libs are pre-downloaded and their licences have been included in the source code. Mirrorr can run on machines with no internet access. 

Support Open Source
