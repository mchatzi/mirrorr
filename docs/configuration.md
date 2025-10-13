## Example source/destinations:
1. `/source/afolder → /dest/`  
   Copy directory afolder _under_ dest. This is the recommended way to keep backups. The --delete flag has effect only for the files and dirs _under_ /dest/afolder (which is created on first run) and siblings of afolder under dest are never touched. For subsequent runs, this config behaves equally to (3), /source/afolder/ -> /dest/afolder/. It doens't require the existence of /dest/afolder the first time it runs.
1. `/media/mysource → /media/mydest`  
   Behaves exactly like (1), as if you had a trailing slash in your dest, /media/mydest**/**
1. `/source/afolder/ → /dest/afolder/`  
   Copy everything found _under_ /source/afolder/, _under_ /dest/afolder/. Both paths must exist prior to running this job. If --delete and percentage allows it, files under /dest/afolder/ that don't exist under /source/afolder/ get deleted. It usually makes sense that both directories are named the same (like in this example, 'afolder'). This is not a recommended config because rsync tries to chgrp the directory /dest/afolder/ at the end of its run, thus easily causing a permissions problem.
1. `/media/mysource/ → /media/mydest`  
   Behaves exactly like (3), as if you had a trailing slash in your dest, /media/mydest**/**
1. `/source/afile.ext → /dest/`  
   Copies the file to dest. Subsequent runs update the file
1. `/source/afile.ext → /dest/otherfile.txe`  
   Both files must exist, replaces contents of otherfile with those of afile

If your paths have spaces, use the space character. Don't use quotes, double quotes or the \\ notation

## Example schedules:
*   Every 20 minutes: `*:0/20`
*   Every hour: `*-*-* *:00:00` or `hourly`
*   Every 2 hours: `0/2:00:00`
*   Every day at 4:30 AM: `*-*-* 4:30:00`
*   Every first of the month at midnight: `*-*-01 00:00:00`
*   Every Monday at 10 PM:`Mon *-*-* 22:00:00`

## Example OpenObserve config:
*   Server: `http://your_o2_url/api/your_org/your_stream_name/_json`
*   Basic Auth: `cm9vdEBlyourGFtcGxlLkeyNvbTpshouldDb2be1wbGVhere4cGFnotzcyDminex9f8jareM7bh0u=m9vdEcrazi48fghj`

An easy way to get the basic auth token: go to your o2 server -> Data sources -> Custom -> Curl.  
Execute the curl command with `--trace -`, and copy the token from curl's output, it's the string after `Authorization: Basic`

## Example Discord config:
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

## Example Uptime Kuma config:

*   Heartbeat server: `http://your_uptime_kuma_url/api/push/abCDeFG?status=up&msg=OK&ping=`
