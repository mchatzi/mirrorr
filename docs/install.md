# Installing Mirrorr

## Bare metal/ Linux containers

### Install
Mirrorr can be installed on any debian based linux system. Before you begin, check the [system requirements](setup.md#system-requirements). 

To get the latest version, run (as root), and from any directory:

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/mchatzi/mirrorr/refs/heads/main/install/install-latest.sh)"
```
    
Mirrorr installs under `/opt/mirrorr` and is run by user `mirrorr` and group `mirrorr`. Mirrorr invokes rsync either as mirrorr or as root. Read more about this [here](setup.md#configuring-mirrorr-user-and-groups)

> During the installation you can set up the username and password for the login screen. See more for that [here](setup.md#logins).

> During the installation you can set up the ssh connection for using remotes. See [here](setup.md#configuring-a-remote-ssh-share).

Upon a successful installation, open Mirrorr in your browser by navigating to http://\<mirrorr-ip>:5000. \<mirrorr-ip> is reported at the end of the installation.

### Install an older version
To install a different than the latest version, find the tag you need [here](https://github.com/mchatzi/mirrorr/tags) and then locally run the install-latest script, passing the tag name (mind the underscore), e.g. 
```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/mchatzi/mirrorr/refs/heads/develop/install/install-latest.sh)" _ v0.7.0-alpha-test
``` 
Or, manually, [download](https://github.com/mchatzi/mirrorr/releases) the release you want, save in any directory, make the `install/install.sh` file executable and run it. After the installation, the directory you downloaded to can be safely deleted. When installing an old release, keep in mind that the documentation found inside the tag (readme and accompanying files) is *more relevant* than the online, latest, documentation.

### Update
It's recommended to run the online installer as it offers the option to update: 

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/mchatzi/mirrorr/refs/heads/main/install/install-latest.sh)"
```

See [releases](https://github.com/mchatzi/mirrorr/releases) for more information when upgrading. If instead you are managing Mirrorr versions manually, you can [download](https://github.com/mchatzi/mirrorr/releases) the tag you want to update to, cd into it and run the installer manually: 
```bash
chmod +x install/install.sh && install/install.sh update
```

### Uninstall
Run uninstall.sh manually, or better via the install-latest installer (choose uninstall): 

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/mchatzi/mirrorr/refs/heads/main/install/install-latest.sh)"
```

On uninstalls, the online installer always runs your local uninstaller, so that is an alternative you can do as well. The local uninstaller is best suited to uninstall your particular version as it was shipped with that version too. Follow the on screen instructions. You have the option to save job data and config.


### Notes for Linux Containers

Running Mirrorr as Linux Container (e.g. as a Proxmox LXC) is ideal. A debian based, unprivileged LXC works great for this. Then just follow the installation on bare-metal guide.

To communicate with storage when Mirrorr runs in Proxmox, mount shares onto the LXC or use ssh shares. Access rights to these shares (at least in Proxmox) is usually done via a known mapped user group. This works because, for example, if user group 44 has write access to a folder in Proxmox host and the folder is mapped into the LXC, then group 100044 inside the LXC container also gets write access. Then any member of the group in the LXC gets write access.

#### _Proxmox LXC Notes_
If using Proxmox, you can paste the html fragment found [here](misc/proxmoxlxc.html), as "notes" in your Proxmox Mirrorr LXC (either through the ui or paste as-is at the beginning of your `/etc/pve/lxc/your-mirrorr-lxc-id.conf`).

## Docker
Docker images are published on [github](https://github.com/users/mchatzi/packages/container/package/mirrorr).

### Install
To install the latest version, download the latest [docker-composer.yml](../install/docker/docker-compose.yml) file and in the same directory, run `docker compose up -d`. This installs the latest version available with some default startup options (see the yaml).

Upon a successful installation, open Mirrorr in your browser by navigating to `http://\<your-docker-host-ip>:5000`. 

Alternatively, run the latest image:
```bash
docker run -d 
    --name mirrorr 
    --restart unless-stopped 
    -p 5000:5000 
    -v mirrorr-data:/opt/mirrorr/data 
    ghcr.io/mchatzi/mirrorr:latest
```

### Install a different version
To install a different than the latest version, specify the tag name in the composer file. Packages can be found [here](https://github.com/users/mchatzi/packages/container/package/mirrorr). 

### Update
Run these in the directory where you downloaded the composer file:

```sh
docker compose pull 
docker compose up -d
```

Or, if you who started Mirrorr with docker run, then pull the new image, remove the old container, and recreate it with the same options and volume:

```sh
docker pull ghcr.io/mchatzi/mirrorr:latest
docker stop mirrorr
docker rm mirrorr
docker run -d .... (repeat your run command)
```

### Uninstall
To uninstall, throw away the Docker container, volume and image.