# Configuring Mirrorr
The following can be configured under settings in the Mirrorr web interface

## Theme
A set of themes to customize your installation

## Reverse cron
Show cron schedules reversed in the home page job listing. For better readability

## Branding
Plain text or html that will be rendered next to the Mirrorr logo. You can inject any html here, no checks are done! This is meant for easier identification between different Mirrorr instances

## Timings
Here you can configure:
- The Scheduler cycle: how often the scheduler checks whether any jobs  need running. Defaults to 1 minute.
- Refresh UI: how often the job list in the homepage auto-refreshes (when autoreload is enabled)
- Keep job logs: how many job logs are kept for each job

## OpenObserve config
OpenObserve can be used as a receiver of job completion events. Example config:
*   Server: `http://your_o2_url/api/your_org/your_stream_name/_json`
*   Basic Auth: `cm9vdEBlyourGFtcGjareM7bh0u=m9vdEcrazi48fghj`

An easy way to get the basic auth token: go to your o2 server -> Data sources -> Custom -> Curl.  
Execute the curl command with `--trace -`, and copy the token from curl's output, it's the string after `Authorization: Basic`

## Discord config
*   Webhook: `https://discord.com/api/webhooks/45678908/tpuyXyrli0y4crziX`
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

## Send Heartbeat usage
If this is filled in, Mirrorr will send a request upon every run of a job, regardless its completion status. Requires a receiving server that supports push notifications (e.g. [Uptime Kuma](https://uptimekuma.org/)). Example Uptime Kuma config:

* Heartbeat server: `http://your_uptime_kuma_url/api/push/abCDeFG?status=up&msg=OK&ping=`

## Remote SSH Port
When ssh shares are used, the port is asked for and registered during the installation process. This field shows the configured port and allows changing it in case you configured ssh keys manually. Changing this port always requires regenrating the ```known_hosts``` file that Mirrorr uses to establish ssh connections. See more on configuring ssh [here](setup.md#configuring-a-remote-ssh-share).

## Server Address
Reports sent to your reporters can contain a link to the job's log file (the variable ```logfile_url```). The host used in that link can be specified here.

