# Installing Mirrorr

## Bare bones/ Linux containers

### Install
Mirrorr can be installed on any debian based linux system. Before you begin, check the [system requirements](docs/setup.md#system-requirements). 

To get the latest version, run (as root), and from any directory:

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/mchatzi/mirrorr/refs/heads/main/install/install-latest.sh)"
```
    
Mirrorr installs under `/opt/mirrorr` and is run by user `mirrorr` and group `mirrorr`. Mirrorr invokes rsync either as mirrorr or as root. Read more about this [here](/docs/setup.md#configuring-mirrorr-user-and-groups)

> During the installation you can set up the username and password for the login screen. See more for that [here](/docs/setup.md#logins).

> During the installation you can set up the ssh connection for using remotes. See [here](/docs/setup.md#configuring-a-remote-ssh-share).

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

