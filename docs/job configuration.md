# Job configuration

## Configuring source and destination
Mirrorr works with both local and remote shares. Remotes must be marked as such using the checkbox in the job configuration UI.

Local paths must be absolute (start with /) and must be writable and their parent folders traversable. For shares that are only readable/writable by specific groups, the mirrorr user may need to be part of those groups. See [Configuring Groups](/docs/setup.md#configuring-mirrorr-user-and-groups).

When using remotes, the path is in the scp format, for example `user@server:/a/b/c/`. Port and password must not be provided here, see [Configuring Remote SSH share](/docs/setup.md#configuring-a-remote-ssh-share). In the examples rules below, path is what follows the ':' character in the scp address, for example in the address mentioned above, the path would be `/a/b/c/`.

### Examples
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

### Autocompletion of paths
Non remote paths use a file browser to list folder contents as you type. The file browser shown can only list locations for which permission is granted, and that depends on whether the mirrorr or root user runs the job.

This is a convenient way to check permissions are correct for the shares your are using and the user running your job. The file browser reports when a folder is not accessible, so this hints that your permissions are not correct. 

When the job is run as root, the permissions checks are run against the root user.

## Schedule
Mirrorr by default runs scheduled jobs, that use a standard 5-field cron syntax: `minute hour day-of-month month day-of-week`. 
A job can also be set to "run manually", by selecting that option in the job configuration UI.

### Example schedules
A few examples of cron schedules:

*   Every 20 minutes: `*/20 * * * *`
*   Every hour: `0 * * * *`
*   Every 2 hours: `0 */2 * * *`
*   Every day at 4:30 AM: `30 4 * * *`
*   Every first of the month at midnight: `0 0 1 * *`
*   Every Friday in May 22:15: `15 22 * May Fri`
*   Every 5th and 15th of the month at 13:30: `30 13 5,15 * *`
*   Hourly from 10:00 to 15:00 (incl), between January and April, on the 1st of the month: `0 10-15 1 Jan-Apr *`

## Deletions
Rsync can be configured to delete on the destination directory. That is, files and folders not existing on source get deleted at the destination. To enable this, tick the `delete` checkbox. 

When deletions are enabled, the allowed percentage check is applied. A number between 0-100 is required here, representing the maximum percentage of files that is allowed to get deleted. In order to run this check, a dry run is performed prior to the real run. As an example, if 30% of files where deleted in source location, and the percentage allowed is set to 20%, then the job will be aborted.

The check is skiped when the rsync job is not set to delete or the allowed percentage is set to 100%.

## Rsync options 
These are options that are passed to the rsync invocation. Only the options that are configurable in the web interface are supported. See rsync manual page for what these options do, or the tip infomration in the job configuration page for a quick reminder.

Sometimes the extras play a crucial role to succesfully executing a job, and sometimes they may require some experimentation. This is mostly depending on the underlying storage, for example, cifs shares will not allow rsync to set a file's date attributes, so the job requires you configure rsync flag `no-times` to true. Remote shares can be even more restrictive.

### Exclusive default options
Mirrorr engine enables some rsync flags unless explicitly disabled:
- `owner` flag is set unless `--no-owner` is checked
- `group` flag is set unless `--no-group` is checked
- `perms` flag is set unless `--no-perms` is checked
- `times` flag is set unless `--no-times` is checked

## Logs
By default, a log is kept always:
- When the job failed or succeeded with warnings (non 0 exit code)
- When the job performed changes and succeeded without any warnings (0 exit code, success)
- When the job succeeded but performed no changes (0 exit code, no-op)

Set "Retention count" to specify how many logs are kept for this job. Mirrorr rotates the logs after that count. Defaults to 10.

Uncheck "log noops" and "log successes" to stop keeping a log for the noop and success statuses respectively.

## Reports
Choose which reporters get notified for this job. By default, reporters get notified when a job has failed or had warnings. 

You can choose to send a report even if the job is successful:
- Select "report successes" to send a report when the job performed changes and succeeded without any warnings
- Select "report noops" when the job succeeded but performed no changes (and thus also had no warnings)

## Modes
- Select "enable job" to enable the job, "dry runs" to run it in dry mode
- Select "run this job as root" to run this job with root privileges
- Select "debug job" to run the job in debug log level mode. With `journalctl -f` you can then see in detail what the job is doing, plus the actual rsync commands that get executed. These commands can be very helpful when setting up ssh shares.
- Nice and ionice can be used to wrap the rsync call in. These can help with reducing cpu and storage stress. A few predefined values are provided for each.

## Skip existence check
Paths, unless remote, always get validated for existence and access. Select this to skip this validation. This is handy when importing or creating a job for which the paths don't yet exist.

