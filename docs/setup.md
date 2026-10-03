# Setting up Mirrorr

## System requirements

A debian based linux system with: systemd, apt, python3 (will install if missing), Python3 venv (will install if missing), rsync (will install if missing), bash, dpkg, ssh-keygen, ssh-keyscan, sudo (will install if missing).

Mirrorr uses systemd for starting its web and backend services. You can find the service file at `/etc/systemd/system/mirrorr-web.service`.

If using non-local sources and/or destinations, you need to ensure rsync is also available in those remote locations too.

- Memory: 512MB- 1GB
- Swap: 512MB-1GB
- Disk: 2GB (primarily used for log files)

## Mirrorr configuration utility
A utility script can be found under `install/mirrorr.sh` in the installation directory (`/opt/mirrorr/`). It can be used for configuring ssh, setting groups for the user running the rsync jobs, reconfiguring the sudo feature, and changing the login credentials.

>This utility is only needed for bare metal/ linux container installations. In docker based installations, environment properties are used instead

Available commands:
- `ssh`: configure ssh connections for remote jobs
- `groups`: set groups for the rsync invocation
- `sudo`: set up running rsync as root
- `unsudo`: disable running rsync as root
- `passwd`: change login credentials

## Logins
Mirrorr is accessed behind a login screen. The credentials are set up during installation or via the mirrorr configuration utility.

>On first installation, and provided you did not set up the credentials when the installer aked, the default credentials are `admin/password`.

To change credentials:
- Bare metal: run the mirrorr configuration utility from within the installation directory (`/opt/mirror/`) with the passwd command:
   ```bash
   install/mirrorr.sh passwd
   ```
- Docker: via environment properties `MIRRORR_LOGIN_USERNAME` and `MIRRORR_LOGIN_PASSWORD`

Credentials are saved in `data/.creds` and the password is hashed. 

To disable login screens and make every Mirrorr page accessible:
- Bare metal: set the following env var to the `[Service]` section of the mirrorr systemd unit: `Environment=MIRRORR_USE_AUTH=false`. Then restart mirrorr service (`systemctl daemon-reload` and `systemctl restart mirrorr-web`).
- Docker: set env property `MIRRORR_USE_AUTH`


## Logs
Job execution logs:
- Check the job logs in the web interface. Errors are reported there
- Use `journalctl -f`, the rsync engine writes logs there as it runs jobs
- Enable debugging (per job, in the UI). Then `journalctl -f` will contain debug level logging for that job
- Enable verbose mode for a job (under rsync options). This will ask rsync to be verbose in its standard output. These outputs are shown in the job logs.

Logs for mirrorr web and backend:
- Do `tail -f /opt/mirrorr/app/web/logs/mirrorr-web-be.log` or use `journalctl -f`. 
- To set/change the log level:
 - Bare metal: add an env var to the `[Service]` section of the mirrorr systemd unit (at `/etc/systemd/system/mirrorr-web.service`). The variable and value is `Environment=MIRRORR_LOG_LEVEL=DEBUG`. After changing this, restart the mirrorr service (`systemctl daemon-reload` and `systemctl restart mirrorr-web`)
 - Docker: set env property `MIRRORR_LOG_LEVEL`

Possible log level values: DEBUG, WARNING, INFO, ERROR, FATAL. Default: WARNING

>Running Mirrorr or jobs in debug mode is not recommended for normal usage and an indication will be shown in the web interface.


## Gunicorn
By default the gunicorn server starts with 1 worker and 4 threads. Only 1 worker is supported. Using more than one workers will trigger multiple schedulers running simultaneously, executing the same jobs at exactly same timings. Mirrorr is not designed for that. 

Additionally, there's currently a per-worker session secret token, so using more than one workers will lead to logouts if your request happens to get served by a different worker.

Logs for the gunicorn server can be seen via `journalctl -f`

To set/change log level:
- Bare metal: by passing `--log-level debug` to gunicorn command line in `/etc/systemd/system/mirrorr-web.service`. Then restart the mirrorr service (`systemctl daemon-reload` and `systemctl restart mirrorr-web`)
- Docker: set env property `GUNICORN_LOG_LEVEL`

Possible log level values: debug, info, warning, error, fatal. Default: warning

## Configuring Mirrorr user and groups
The Mirrorr application is run by user `mirrorr`, but invocations of rsync can be executed either as this user or with root privileges. 

When rsync is run as a non root user, it *does not preserve* the owner and group of the synced files at the destination. To have rsync preserve these attributes, it must be run as root.

### Running Jobs as the mirrorr user
This is the default and it's suitable when you don't care about preserving owner and group, or if running rsync with elevated rights violates security in your system. The rsync invocation happens as user `mirrorr` and using any (and all) user groups the mirrorr user belongs to. The items in destination will be owned by the id and gid of the mirrorr user and group respectively.

### Running Jobs as root
To run a job as root, first make sure the feature is enabled (see below) and then simply check the "run as root" option in the job configuration UI. Root uses the same user groups that are configured for the mirrorr user. Items in the destination will preserve owner and group from source.

### Configuring Groups
In many storage setups, access to a share is governed by user groups. To allow Mirrorr app to access those shares, the user running rsync needs to belong to these groups. If that user is the root user, then usually no user groups need to be specified. It is needed however in cases where Mirrorr runs in a containerized environment like Linux Containers and Docker when ran rootless or when user namespace mapping is configured.

#### Bare metal/ Linux containers
Add all the needed groups by executing the mirrorr utility with the groups command:
```bash
install/mirrorr.sh groups
```
Groups can be removed manually (`usermod -rG group-name mirrorr`).

#### Docker
Groups can be specified via theirs *gid*s as a comma separated list in environment variable `MIRRORR_USERGROUPS`, e.g. `MIRRORR_USERGROUPS: "1005,10000,33"`

### Enabling/disabling root invocations
Enabling root invocations can expose you to security risks. When enabled:
- a group named `mirrorr-sudo` is created and user mirrorr is added to it
- file `/etc/sudoers.d/mirrorr-sudo` is created, with rules on what mirrorr-sudo group can do with root privileges.

>If you disable the feature, make sure you don't have any jobs with "run this job as root" set, as those will now give errors.

#### Bare metal/ Linux containers
To enable root invocations, run the mirrorr utility with the sudo command:
```bash
install/mirrorr.sh sudo
```

To disable root invocations run the unsudo command:
```bash
install/mirrorr.sh unsudo
```

#### Docker
Enable or disable roor invocations by setting the environment variable 
`MIRRORR_ENABLE_SUDO` to "true" or "false"


## Configuring a remote SSH share
The installer asks for setting up the ssh keys and all configuration needed for remote connections. Mirrorr can connect to ssh shares via  keys only (no password). For Docker based installations, the manual setup needs to be followed, see end of section.

> Before configuring Mirrorr, ensure you have a working remote ssh share by confirming the ssh connection and invoking an rsync operation manually from the terminal.

During the configuration of ssh you will need to (when asked to):
1. Copy the public key that is shown to the remote machine and supply it to the ssh server
2. Fill in the ip/hostname and port that you want Mirrorr to use

### Bare metal
If you don't set up ssh during install, you can either:
- Set up via the mirrorr utility and the ssh command (highly recommended):
   ```bash
   install/mirrorr.sh ssh
   ```
- Set up ssh all manually


### Docker installations
With docker, it is required you follow the manual steps below. The ssh configuration results in a few files being generated in the ssh folder of Mirrorr app. This folder needs to be generated outside of the container and mapped into it, to `/opt/mirrorr/data/ssh`. Example:
```yaml
volumes:
  - /a_folder/on_docker_host/with_all_the/ssh_config:/opt/mirrorr/data/ssh
```
Alternatively, create and use a folder named ssh under the folder you mapped via the env property `MIRRORR_DATA`, as that variable already maps to the parent folder /opt/mirrorr/data.

All the manual ssh setup described below can be followed but paths need to adjusted to write into the ssh_config folder (assuming the example path above).

### Manual ssh setup:
The steps below are same for both bare metal and docker installations.

>For Docker based installations, replace the path `/opt/mirrorr/data/ssh` with the folder that you mapped as the ssh folder into the docker container

1. In Mirrorr's machine, open a terminal 
1. Temporarily change permissions for the ssh directory: 
   ```bash
   chmod 700 /opt/mirrorr/data/ssh
   ```
1. Create a public key, without a passphrase: 

   ```bash
   ssh-keygen -N '' -t ed25519 -f /opt/mirrorr/data/ssh/id_ed25519 -C myremote
   ```
   
   Copy this key (the content) and register it to the remote ssh server.
   
   The ssh connection is established using public keys for the mirrorr user, which is the (linux) user Mirrorr runs as. No password authentication is assumed from the remote end, thus it's also not supported in Mirrorr.
1. If this is not the first time configuring this, clean up any previous/stale entries for this server and port with:
   ```bash
   ssh-keygen -R "[yourremotehost:32222]" -f /opt/mirrorr/data/ssh/known_hosts
   ```
1. Connect to remote and store the known_hosts file, We assume a port and host here: 
   
   ```bash
   sh-keyscan -H -p 32222 yourremotehost >> /opt/mirrorr/data/ssh/known_hosts
   ```
1. Do `chmod 400 /opt/mirrorr/data/ssh/known_hosts`
1. If not a docker based installation: Do `chown mirrorr:mirrorr /opt/mirrorr/data/ssh/known_hosts`
1. Put back the restricted permissions to the ssh directory:
   ```bash
   chmod 500 /opt/mirrorr/data/ssh
   ```
1. Head on to settings in mirrorr web interface and configure the port that your remote server is using, e.g. Remote SSH Port: 32222
1. Restart mirrorr service with `systemctl restart mirrorr-web` or your docker container
