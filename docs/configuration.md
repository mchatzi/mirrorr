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
To use the Discord reporter, you first need the url of a webhook from your Discord account.
*   Webhook: paste here the url, e.g. `https://discord.com/api/webhooks/45678908/tpuyXyrli0y4crziX`
*   Template: a valid discord webhook template. Mirrorr supports many placeholders that you can use to supply your report with job status information. Below you can see an example that showcases **every** possible variable made available via mirrorr):
    ```json
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
 Mirrorr can send send a request to a server upon every execution of a job. This is meant to be used in combination with a receiving end, e.g. a monitor application that supports push notifications, like [Uptime Kuma](https://uptimekuma.org/). Then a monitor can be configured there to check, on a fixed interval, whether mirrorr jobs have executed. 
 
To enable this, fill in the "Heartbeat server" to the url of your service. For UptimeKuma this could be for example:
```
http://your_uptime_kuma_url/api/push/abCDeFG?status=up&msg=OK&ping=
```
Mirrorr will send a GET request to this url every time a job is executed (upon completion), regardless of the job's completion status.

Specifically for UptimeKuma urls, it is possible to set the status and msg of the push url, based on:
- the status of the completed job that is triggering the push. To enable that, check "send job status" under the Send Heartbeat section. 
- the status of any reporters ran upon completion. To enable that, check "send reporters status" under the Send Heartbeat section. 

>If both "send job status" and "send reporters status" are set and a job failed, the heartbeat won't check if any reporter failed. It is more important to report the failed job.

>When either of these are set, your monitor in UptimeKuma will notify you on failed jobs or failed reporting, but this is ephemeral, as _any_ subsequent, and successful, job, will reset your monitor to healthy state again. Thus, using this feature as a _job status reporter_ is not as powerful as using a dedicated reporter (o2, discord) _per job_. This is mostly meant to answer the question "_is mirrorr up and executing my jobs_".

## Remote SSH Port
When ssh shares are used, the port is asked for and registered during the installation process. This field shows that port and allows changing it in case you are configuring ssh keys manually. Changing this port always requires regenerating the `known_hosts` file that Mirrorr uses to establish ssh connections. See more on configuring ssh [here](setup.md#configuring-a-remote-ssh-share).

## Server Address
Reports sent to your reporters can contain a link to the job's log file (the variable `logfile_url`). The host used in that link can be specified here.

