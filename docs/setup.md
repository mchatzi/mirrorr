# Setting up Mirrorr

## Global Log level
You can set the Mirrorr engine in global debug mode. Add an env var to the [Service] section of the mirrorr systemd unit (at ```/etc/systemd/system/mirrorr-web.service```). The variable and value is ```Environment=MIRRORR_LOG_LEVEL=DEBUG```. Running the app in debug mode is not recommended for normal usage and an indication will be shown in the web interface.

## Gunicorn
Not much to configure here. By default the gunicorn server starts with 1 worker and 4 threads. Only 1 worker is supported. Using more than one workers will trigger multiple schedulers running simultaneously, executing the same jobs at exactly same timings. Mirrorr is not designed for that. 

Additionally, there's currently a per-worker session secret token, so using more than one workers will lead to logouts if your request happens to get served by a different worker.

To see logs for the gunicorn server use ```journalct -f```, and to set a different log level for it, eg debug, pass ```--log-level debug``` to gunicorn command line in ```/etc/systemd/system/mirrorr-web.service```.

## Configuring Groups
The installer ask for groups that the mirrorr user should be part of. This is intended for granting access to mirrorr user when those groups are the only means to get access to a local share. In case you need to add those groups manually, run ```install/mirrorr.sh groups``` from within the installation directory (```/opt/mirror/```) and follow the instrcutions.

## Configuring a remote SSH share
The installer asks for setting up the ssh keys and all configuration needed for remote connections. Mirrorr can connect to ssh shares via  keys only (no password). 

Before configuring this, ensure you have a working remote ssh share by confirming the ssh connection and invoking rsync manually from the terminal.

During the installation you will need to (when asked to):
1. Copy the public key that is shown to the remote machine and supply it to the ssh server
2. Fill in the port that you want Mirrorr to use

If you don't set up ssh during install, you can later:
- Run ```install/mirrorr.sh ssh``` from within the installation directory (```/opt/mirror/```) and follow the instrcutions
- Run the installer again
- Set up ssh all manually

Here's how to do it manually (in a debian system):
1. In Mirrorr's machine, open a terminal 
1. Temporarily change permissions for the ssh directory: 

   ```chmod 700 /opt/mirrorr/data/ssh```
1. Create a public key, without a passphrase, for mirrorr user and your "myremote": 

   ```su -s /bin/sh mirrorr -c "ssh-keygen -N "" -t ed25519 -f /opt/mirrorr/data/ssh/id_ed25519 -C myremote"```
   
   The ssh connection is established using public keys for the mirrorr user, which is the (linux) user Mirrorr runs as. No password authentication is assumed from the remote end, thus it's also not supportd in Mirrorr.
1. Connect to remote and store the known_hosts file, We assume port and host here: 
   
   ```sh-keyscan -H -p 32222 yourremotehost >> /opt/mirrorr/data/ssh/known_hosts```

   Optionally clean up any previous entries for this server and port with

   ```ssh-keygen -R "[yourremotehost:32222]" -f /opt/mirrorr/data/ssh/known_hosts```
1. Do ```chmod 400 /opt/mirrorr/data/ssh/known_hosts```
1. Do ```chown mirrorr:mirrorr /opt/mirrorr/data/ssh/known_hosts```
1. Put back the restricted permissions to the ssh directory: ```chmod 500 /opt/mirrorr/data/ssh```
1. Copy the public key that was given during the installation or update to the remote machine and supply it to the ssh server
1. Head on to settings in mirrorr web interface and configure the port that your remote server is using, e.g. Remote SSH Port: 32222

## Proxmox LXC notes
Running Mirrorr in a Proxmox LXC is ideal. You can find an html fragment [here](proxmoxlxc.html), that you can paste as "notes" in your lxc (either through the ui or paste at the beginning of your ```/etc/pve/lxc/your-mirrorr-lxc-id.conf```).
