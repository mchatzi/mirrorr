## Example schedules:
- Every 20 minutes: ```*:0/20```
- Every hour: ```*-*-* *:00:00``` or ```hourly```
- Every 2 hours: ```0/2:00:00```
- Every day at 4:30 AM: ```*-*-* 4:30:00```
- Every first of the month at midnight: ```*-*-01 00:00:00```
- Every Monday at 10 PM:```Mon *-*-* 22:00:00```

## Example OpenObserve config:
- Server: ```http://your_o2_url/api/your_org/your_stream_name/_json```
- Basic Auth: ```cm9vdEBlyourGFtcGxlLkeyNvbTpshouldDb2be1wbGVhere4cGFnotzcyDminex9f8jareM7bh0u=m9vdEcrazi48fghj```

An easy way to get the basic auth token: go to your o2 server -> Data sources -> Custom -> Curl.  
Execute the curl command with ```--trace -```, and copy the token from curl's output, it's the string after ```Authorization: Basic ```
  
## Example Discord config:
- Webhook: ```https://discord.com/api/webhooks/4379990012345678908/abCdE_fG_HJklnotM_N_oprmyt5Qr_StuvRkey3Q-tpuyXyrli0y4crziX```
- Template (showcasing **every** possible variable made available via mirrorr):
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

#### Example Uptime Kuma config:
- Heartbeat server: ```http://your_uptime_kuma_url/api/push/abCDeFG?status=up&msg=OK&ping=```
