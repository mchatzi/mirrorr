## Configuring job source and destination
Mirrorr handles both local and remote shares. 

Local paths must be absolute (start with /) and must be writable and their parent folders traversable. Depending on the underlying storage, switch on and off rsync flags to ensure the job runs correctly. For example, cifs shares will not allow rsync to set a file's date attributes, so the job requires you configure rsync flag ```no-times``` to true.

For shares that are only readable/writable by specific groups, mirrorr will need to be part of those groups. See [Configuring Groups](/docs/configuration.md#configuring-groups)

When using remotes, the path is in the scp format, for example ```user@server:/a/b/c/```. No port and password can be provided, see [Configuring Remote SSH share](/docs/configuration.md#configuring-remote-ssh-share). In the examples rules below, path is what follows the ':' character in the scp address, for exmaple in the address mentioned above, the path would be ```/a/b/c/```.


Some examples of paths, and how rsync behaves when syncing folders vs files, and having trailing spaces versus not:

1. `/source/afolder → /dest/`  
   Copy directory afolder _under_ dest. This is the recommended way to keep backups. The --delete flag has effect only for the files and dirs _under_ /dest/afolder (which is created on first run) and siblings of afolder under dest are never touched. For subsequent runs, this config behaves equally to the config shown in (3): /source/afolder/ -> /dest/afolder/. This config doens't require the existence of /dest/afolder the first time it runs.
1. `/media/mysource → /media/mydest`  
   Behaves exactly like (1), as if you had a trailing slash in your dest: /media/mydest/
1. `/source/afolder/ → /dest/afolder/`  
   Copy everything found _under_ /source/afolder/, _under_ /dest/afolder/. Both paths must exist prior to running this job. If --delete and percentage allows it, files under /dest/afolder/ that don't exist under /source/afolder/ get deleted. It usually makes sense that both directories are named the same (like in this example, 'afolder'). This is not a recommended config because rsync tries to chgrp the directory /dest/afolder/ at the end of its run, thus easily causing a permissions problem.
1. `/media/mysource/ → /media/mydest`  
   Behaves exactly like (3), as if you had a trailing slash in your dest: /media/mydest/
1. `/source/afile.ext → /dest/`  
   Copies the file to dest. Subsequent runs update the file
1. `/source/afile.ext → /dest/otherfile.txe`  
   Both files must exist, replaces contents of otherfile.txe with those of afile.ext

If your paths have spaces, use the space character. Don't use quotes, double quotes or the \\ notation


## Example schedules
In job configutations, ```Schedule``` expects the format used in systemd's timer's ```OnCalendar``` entries. Examples:

*   Every 20 minutes: `*:0/20`
*   Every hour: `*-*-* *:00:00` or `hourly`
*   Every 2 hours: `0/2:00:00`
*   Every day at 4:30 AM: `*-*-* 4:30:00`
*   Every first of the month at midnight: `*-*-01 00:00:00`
*   Every Monday at 10 PM:`Mon *-*-* 22:00:00`

Schedule timers are set in user scope. The user (and group) that the mirrorr services use is mirrorr:mirrorr. Lingering services are used, so the timers fire regardless if a user is logged in to the host machine or not.

## Example OpenObserve config
*   Server: `http://your_o2_url/api/your_org/your_stream_name/_json`
*   Basic Auth: `cm9vdEBlyourGFtcGxlLkeyNvbTpshouldDb2be1wbGVhere4cGFnotzcyDminex9f8jareM7bh0u=m9vdEcrazi48fghj`

An easy way to get the basic auth token: go to your o2 server -> Data sources -> Custom -> Curl.  
Execute the curl command with `--trace -`, and copy the token from curl's output, it's the string after `Authorization: Basic`

## Example Discord config
*   Webhook: `https://discord.com/api/webhooks/4379990012345678908/abCdE_fG_HJklnotM_N_oprmyt5Qr_StuvRkey3Q-tpuyXyrli0y4crziX`
*   Template (showcasing **every** possible variable made available via mirrorr):

```
{
  "embeds": [
    {
      "title": "❗ {status} ❗",
      "description": "Report for job **{name}**",
      "color": 15783023,
      "footer": {
        "text": "Date/timestamp: {timestamp_human_friendly}/{timestamp}\nSource: {source}\nDest: {dest}"
      },
      "fields": [
        {
          "name": "Exit code",
          "value": "{exit_code}"
        },
        {
          "name": "Exit message",
          "value": "{message}"
        },
        {
          "name": "Files Info",
          "value": "Transferred: {transferred}, Created: {created}\nDeleted: {deleted}, Total: {total_files}"
        },
        {
          "name": "Bytes Info Human Readable / number",
          "value": "{human_readable_bytes_transferred} / {bytes_transferred}"
        },
        {
          "name": "Job duration human readable / ms",
          "value": "{human_readable_duration} / {duration}"
        },
        {
          "name": "Logfile",
          "value": "{logfile_url}"
        }
      ]
    }
  ]
}
```

## Example Heartbeat usage
Requires a receiving server that supports push notifications (e.g. [Uptime Kuma](https://uptimekuma.org/)). Example Uptime Kuma config:

*   Heartbeat server: `http://your_uptime_kuma_url/api/push/abCDeFG?status=up&msg=OK&ping=`

## Configuring Groups
The installer (and updater) ask for groups that the mirrorr user should be part of. This is intended for granting access to mirrorr user when those groups are the only means to get access to a local share. In case you need to add those groups manually, and assuming for example that your group is named ```my_group_with_access_to_my_cifs_share```, add the mirrorr user to that group by running ```usermod -aG my_group_with_access_to_my_cifs_share mirrorr```.

## Configuring Remote SSH share
The installer (and updater) asks for setting up the ssh keys and all configuration needed for remote connections. Assuming you did that, then no more configuration is needed. The public key that was given during the installation or update needs to be copied to remote machine and supplied to the ssh server.

Assuming you did not set up ssh during install, you can either:
- Run the updater, as it will also ask you to set it up
- Do it manually

Here's how to do it manually ( in a debian system):
- In Mirrorr's machine, open a terminal 
- Temporarily change permissions for the ssh directory: ```chmod 700 /opt/mirrorr/data/ssh```
- Create a public key, without a passphrase, for mirrorr user and your "myremote":
```su -s /bin/sh mirrorr -c "ssh-keygen -N "" -t ed25519 -f /opt/mirrorr/data/ssh/id_ed25519 -C myremote"```
The ssh connection is established using public keys for the mirrorr user, which is the (linux) user Mirrorr runs as. No password authentication is assumed from the remote end, thus it's also not supportd in Mirrorr.
- Connect to remote and store the known_hosts file, We assume port and host here: ```sh-keyscan -H -p 32222 yourremotehost >> /opt/mirrorr/data/ssh/known_hosts```. Optionally clean up any previous entries for this server and port with ```ssh-keygen -R "[yourremotehost:32222]" -f /opt/mirrorr/data/ssh/known_hosts```
- Do ```chmod 400 /opt/mirrorr/data/ssh/known_hosts```
- Do ```chown mirrorr:mirrorr /opt/mirrorr/data/ssh/known_hosts```
- Put back the restricted permissions to the ssh directory: ```chmod 500 /opt/mirrorr/data/ssh```
- Head on to settings in mirrorr web interface and configure the port that your remote server is using, e.g. Remote SSH Port: 32222
