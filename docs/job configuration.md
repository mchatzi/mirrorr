# Job configuration

## Configuring source and destination
Mirrorr works with both local and remote shares. Remotes must be marked as such using the checkbox in the ui.

Local paths must be absolute (start with /) and must be writable and their parent folders traversable. For shares that are only readable/writable by specific groups, mirrorr will need to be part of those groups. See [Configuring Groups](/docs/setup.md#configuring-groups)

When using remotes, the path is in the scp format, for example ```user@server:/a/b/c/```. Port and password must not be provided here, see [Configuring Remote SSH share](/docs/setup.md#configuring-a-remote-ssh-share). In the examples rules below, path is what follows the ':' character in the scp address, for exmaple in the address mentioned above, the path would be ```/a/b/c/```.


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
In job configurations, ```Schedule``` uses standard 5-field cron syntax: `minute hour day-of-month month day-of-week`. Examples:

*   Every 20 minutes: `*/20 * * * *`
*   Every hour: `0 * * * *`
*   Every 2 hours: `0 */2 * * *`
*   Every day at 4:30 AM: `30 4 * * *`
*   Every first of the month at midnight: `0 0 1 * *`
*   Every Monday at 10:15 PM: `15 22 * * Mon`

## Deletions
Rsync can be configured to delete on the destination directory. That is, files and folders not existing on source get deleted at the destination. To enable this, tick the ```delete``` checkbox. 

When deletions are enabled, the allowed percentage check is applied. A number between 0-100 is required here, representing the maximum percentage of files that is allowed to get deleted. In order to run this check, a dry run is performed prior to the real run. As an example, if 30% of files where deleted in source location, and the percentage allowed is set to 20%, then the job will be aborted.

The check is skiped when the rsync job is not set to delete or the allowed percentage is set to 100%.

## Rsync extras 
These are options that are passed to the rsync invocation. Only the options that are configurable in the web interface are supported. See rsync manual page for what these options do, or the tip infomration in the job configuration page for a quick reminder.

Sometimes the extras play a crucial role to succesfully executing a job, and sometimes they may require some experimentation. This is mostly depending on the underlying storage, for example, cifs shares will not allow rsync to set a file's date attributes, so the job requires you configure rsync flag ```no-times``` to true. Remote shares can be even more restrictive.

## Reporters
Choose which reporters get notified for this job

## Debug mode
The job will run in debug log level mode. With ```journalctl -f``` you can then see in detail what the job is doing, plus the actual rsync commands that get executed. These commands can be very helpful when setting up ssh shares.

## Skip existence check
Paths, unless remote, always get validated for existence and access. Select this to skip this validation. This is handy when importing or creating a job for which the paths don't yet exist.

