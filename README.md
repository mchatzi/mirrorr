# Mirrorr
Mirrorr is an orchestrator for rsync jobs. Plus a thin web frontend for managing all that. 
It supports configuring and scheduling rsync invocations.

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

## Install

Mirrorr runs on Linux only. The installers check for the existence of systemd and Mirrorr relies on that system for starting its web and backend services.

1. To get the latest version, run (as root), from any directory

    ```bash -c "$(wget -qLO - https://raw.githubusercontent.com/mchatzi/mirrorr/refs/heads/main/install/install-latest.sh)"```
    
    Mirrorr installs under ```/opt/mirrorr``` and is run by user ```mirrorr``` and group ```mirrorr```.

    During installation you are asked to specify any user groups the ```mirrorr``` user should belong to. See more for that [here](/docs/setup.md#configuring-groups).  Additionally, during the installation you can set up the ssh connection for using remotes. See [here](/docs/setup.md#configuring-remote-ssh-share).
   
    To install a different version, [download](https://github.com/mchatzi/mirrorr/releases) the release you need, save in any directory, make the ```install/install.sh``` file executable and run it. After the installation, the directory you downloaded to can be safely deleted. When installing an old release, keep in mind that the documentation found inside the tag (readme and accompanying files) is *more relevant* than the online, latest, documentation.

2. Access the Frontend:
Open your browser and navigate to http://\<your-ip>:5000
(replace <your-ip> with the IP address of the machine running Mirrorr, as reported at the end of the installation).


## Use
* Backup files and folders, local or remotely, fast (delta)
* Share files - setup shared remote folders
* Create/edit/view/schedule/import/export/copy/kill file mirror jobs across local and remote file shares
* Dry-run support. Configurable threshold (percentage of deleted files in source), that aborts the job if exceeded 
* Configurable reporting with [OpenObserve](https://openobserve.ai/) and [Discord webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) 
* Heartbeat utility. Mirrorr sends a heartbeat every time a job runs, so you know it's up and running
* Rich set of rsync flags supported (configurable per job)

See [configuration](/docs/configuration.md) and [job configuration](/docs/job%20configuration.md).

## Logs
Job execution logs:
- Check the job logs in the web interface. Errors are reported there
- Use ```journalctl```, the rsync engine writes logs there as it runs jobs
- Enable debugging (per job, in the UI). Then ```journalctl``` will contain debug level logging for that job
- Enable verbose mode for a job (under rsync options). This will ask rsync to be verbose in its standard output. These outputs are shown in the job logs.

Logs for mirrorr web and backend:
- Do ```tail -f /opt/mirrorr/app/web/logs/mirrorr-web-be.log``` or use ```journalctl```. 
- To set/change the log level, add an env var to the ```[Service]``` section of the mirrorr systemd unit (at ```/etc/systemd/system/mirrorr-web.service```). The variable and value is ```Environment=MIRRORR_LOG_LEVEL=DEBUG```. Possible values: DEBUG, WARNING, INFO, ERROR, FATAL

Logs for the gunicorn server:
- Use ```journalctl```
- Set/change log level by passing ```--log-level debug``` to gunicorn command line in ```/etc/systemd/system/mirrorr-web.service```. Possible values: debug, info, warning, error, fatal

## Update
It's recommended to run the online installer as it offers the option to update: 

```bash -c "$(wget -qLO - https://raw.githubusercontent.com/mchatzi/mirrorr/refs/heads/main/install/install-latest.sh)"```

See [releases](https://github.com/mchatzi/mirrorr/releases) for more information when upgrading. If instead you are managing Mirrorr versions manually, you can [download](https://github.com/mchatzi/mirrorr/releases) the tag you want to update to, cd into it and run the installer manually: 
```chmod +x install/install.sh && install/install.sh update```

## Uninstall
Run uninstall.sh manually, or better via the install-latest installer (choose uninstall): 

```bash -c "$(wget -qLO - https://raw.githubusercontent.com/mchatzi/mirrorr/refs/heads/main/install/install-latest.sh)"```

On uninstalls, the online installer always runs your local uninstaller, so that is an alternative you can do as well. The local uninstaller is best suited to uninstall your particular version as it was shipped with that version too. Follow the on screen instructions. You have the option to save job data and config.

## Backups
To make a backup of all your jobs and configuration, simply copy everything under ```/opt/mirrorr/data```. You could even have a mirrorr job to do that... All runtime data is stored there and this directory is not touched during updates.

There are also export and import buttons: in settings page, to export/import settings, as well as in the job details page, to export/import jobs.

## Contributions
I kept the code as simple as possible. No external libs. Back to basics. The code is meant to be:
- Dead simple, especially the FE
- Hopefully extremely fast
- Hopefully ridiculously light on your machine and browser
- Fragile, I do very few validations and very few checks. Not sticking to only what the app does (eg by calling the mirrorr web api yourself) can definitely have unfortunate outcomes. Don't break the mirrorr!

Please contribute? See roadmap [here](https://github.com/mchatzi/mirrorr/issues/3)

## License
Mirrorr is licensed under the AGPL-3.0 license. For more details, see the [LICENSE](https://github.com/mchatzi/mirrorr/blob/main/LICENCE)  
  
Mirrorr web interface loads zero external scripts/css/fonts/imgs. Some fonts/libs are pre-downloaded and their licences have been included in the source code. Mirrorr can run on machines with no internet access. 

Support Open Source
