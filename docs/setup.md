# Setting up Mirrorr

## System requirements

A debian based linux system with: systemd, apt, python3 (will install if missing), Python3 venv (will install if missing), rsync (will install if missing), bash, dpkg, ssh-keygen, ssh-keyscan, sudo (will install if missing).

Mirrorr uses systemd for starting its web and backend services. You can find the service file at ```/etc/systemd/system/mirrorr-web.service```.

If using non-local sources and/or destinations, you need to ensure rsync is also available in those remote locations too.

- Memory: 512MB- 1GB
- Swap: 512MB-1GB
- Disk: 2GB (primarily used for log files)

## Mirrorr configuration utility
A utility script can be found under ```install/mirrorr.sh``` in the installation directory (```/opt/mirrorr/```). This can be used for configuring ssh, setting groups for mirrorr user, reconfiguring the sudo feature, and changing the login credentials.

## Logins
Mirrorr is accessed behind a login screen. The credentials are set up during installation or via the mirrorr configuration utility.

>On first installation, and provided you did not set up the credentials when the installer aked, the default credentials are ```admin/password```.

To change credentials, run the mirrorr configuration utility: ```install/mirrorr.sh passwd``` from within the installation directory (```/opt/mirror/```) and follow the instructions. Credentials are saved in ```data/.creds``` and the password is hashed. 

To disable login screens and make every Mirrorr page accessible, set the following env var to the ```[Service]``` section of the mirrorr systemd unit: ```Environment=MIRRORR_USE_AUTH=false``` 

Then restart mirrorr service (```systemctl daemon-reload``` and ```systemctl restart mirrorr-web```).


## Logs
Job execution logs:
- Check the job logs in the web interface. Errors are reported there
- Use ```journalctl -f```, the rsync engine writes logs there as it runs jobs
- Enable debugging (per job, in the UI). Then ```journalctl -f``` will contain debug level logging for that job
- Enable verbose mode for a job (under rsync options). This will ask rsync to be verbose in its standard output. These outputs are shown in the job logs.

Logs for mirrorr web and backend:
- Do ```tail -f /opt/mirrorr/app/web/logs/mirrorr-web-be.log``` or use ```journalctl -f```. 
- To set/change the log level, add an env var to the ```[Service]``` section of the mirrorr systemd unit (at ```/etc/systemd/system/mirrorr-web.service```). The variable and value is ```Environment=MIRRORR_LOG_LEVEL=DEBUG```. Possible values: DEBUG, WARNING, INFO, ERROR, FATAL. After changing this, restart the mirrorr service (```systemctl daemon-reload``` and ```systemctl restart mirrorr-web```).

>Running the app in debug mode is not recommended for normal usage and an indication will be shown in the web interface.


## Gunicorn
By default the gunicorn server starts with 1 worker and 4 threads. Only 1 worker is supported. Using more than one workers will trigger multiple schedulers running simultaneously, executing the same jobs at exactly same timings. Mirrorr is not designed for that. 

Additionally, there's currently a per-worker session secret token, so using more than one workers will lead to logouts if your request happens to get served by a different worker.

Logs for the gunicorn server:
- Use ```journalctl -f```
- Set/change log level by passing ```--log-level debug``` to gunicorn command line in ```/etc/systemd/system/mirrorr-web.service```. Possible values: debug, info, warning, error, fatal. Then restart the mirrorr service (```systemctl daemon-reload``` and ```systemctl restart mirrorr-web```)


## Configuring Mirrorr user and groups
The Mirrorr application is run by user ```mirrorr```, but invocations of rsync can be executed either as this user or with root privileges. 

When rsync is run as a non root user, it *does not preserve* the owner and group of the synced files at the destination. To have rsync preserve these attributes, it must be run as root.

### Running Jobs as the mirrorr user
This is the default and it's suitable when you don't care about preserving owner and group, or if running rsync with elevated rights violates security in your system. The rsync invocation happens as user ```mirrorr``` and using any (and all) user groups the mirrorr user belongs to. 

### Running Jobs as root
To run a job as root, check the "Run rsync as root" option in the job configuration UI. Root can use any user groups, this is specified also in same UI.

### Configuring Groups
In many storage setups, access to a share is governed by user groups. To allow Mirrorr app to access those shares, the user running rsync needs to belong to these groups.
- For an rsync job that runs by root: add these groups in the job configuration UI
- For all jobs run by mirrorr user: add all the needed groups by executing ```install/mirrorr.sh groups``` from within the installation directory (```/opt/mirror/```) and following the instructions. Groups added to mirrorr user can only be removed manually (```usermod -rG group-name mirrorr```).

### Removing all sudoers config
In case where security does not allow configuring sudo on your system, you may want to revert what the installer configured, in the order shown:
- Remove mirrorr user from sudo group: ```usermod -rG mirrorr-sudo mirrorr```
- Remove the custom sudo rule: ```rm /etc/sudoers.d/mirrorr-sudo```
- Delete the group: ```groupdel mirrorr-sudo``` 

>Make sure you don't have any jobs with "Run rsync as root" set, as those will now give errors.

To bring back the sudo configuration, execute ```install/mirrorr.sh sudo``` from within the installation directory (```/opt/mirror/```) and follow the instructions. 


## Configuring a remote SSH share
The installer asks for setting up the ssh keys and all configuration needed for remote connections. Mirrorr can connect to ssh shares via  keys only (no password). 

> Before configuring Mirrorr, ensure you have a working remote ssh share by confirming the ssh connection and invoking an rsync operation manually from the terminal.

During the installation you will need to (when asked to):
1. Copy the public key that is shown to the remote machine and supply it to the ssh server
2. Fill in the ip/hostname and port that you want Mirrorr to use

If you don't set up ssh during install, you can later:
- Set up via the utility: ```install/mirrorr.sh ssh``` (from within the installation directory ```/opt/mirror/```) and follow the instructions
- Run the installer again (and set up ssh when the installer asks)
- Set up ssh all manually

Here's how to do it manually (in a debian system):
1. In Mirrorr's machine, open a terminal 
1. Temporarily change permissions for the ssh directory: 

   ```chmod 700 /opt/mirrorr/data/ssh```
1. Create a public key, without a passphrase, for mirrorr user and your "myremote": 

   ```su -s /bin/sh mirrorr -c "ssh-keygen -N '' -t ed25519 -f /opt/mirrorr/data/ssh/id_ed25519 -C myremote"```
   
   Copy this key (the content) and register it to the remote ssh server.
   
   The ssh connection is established using public keys for the mirrorr user, which is the (linux) user Mirrorr runs as. No password authentication is assumed from the remote end, thus it's also not supported in Mirrorr.
1. Connect to remote and store the known_hosts file, We assume a port and host here: 
   
   ```sh-keyscan -H -p 32222 yourremotehost >> /opt/mirrorr/data/ssh/known_hosts```

   > Optionally (do this first) clean up any previous/stale entries for this server and port with ```ssh-keygen -R "[yourremotehost:32222]" -f /opt/mirrorr/data/ssh/known_hosts```
1. Do ```chmod 400 /opt/mirrorr/data/ssh/known_hosts```
1. Do ```chown mirrorr:mirrorr /opt/mirrorr/data/ssh/known_hosts```
1. Put back the restricted permissions to the ssh directory: ```chmod 500 /opt/mirrorr/data/ssh```
1. Head on to settings in mirrorr web interface and configure the port that your remote server is using, e.g. Remote SSH Port: 32222
1. Restart mirrorr service: ```systemctl restart mirrorr-web```

## Running in Proxmox

Running Mirrorr in a Proxmox LXC is ideal. A debian based, unprivileged LXC works great. To communicate with storage when Mirrorr runs in Proxmox, mount shares onto the LXC or use ssh shares. 

Access rights to mounted shares in Proxmox is usually done via a known mapped user group. This works because, for example, if user group 44 has write access to a folder in Proxmox host and the folder is mapped into the LXC, then group 100044 inside the LXC container also gets write access. Then any member of the group in the LXC gets write access.

### LXC Notes
You can find an html fragment [here](proxmoxlxc.html), that you can paste as "notes" in your Proxmox Mirrorr LXC (either through the ui or paste as-is at the beginning of your ```/etc/pve/lxc/your-mirrorr-lxc-id.conf```).
