# Custom Reporters

Below you can find many examples of custom reporters for different known notification and alert providers.


## OpenObserve reporter
OpenObserve can be used as a receiver of job completion events using their json receiving endpoint.

Assuming **endpoint url** `http://your_o2_url/api/your_org/your_stream_name/_json` and auth token `9tZTpNIU4pJCRPcGVub2JzZXJ2ZQ`:
- create a **post** method endpoint and fill in the url
- leave both **param name** and **template** empty
- **headers**: `Authorization: Basic 9tZTpNIU4pJCRPcGVub2JzZXJ2ZQ`.

That's it. Your O2 instance will now be receiving reports once you configure a job to using this reporter.

An easy way to get the basic auth token for O2 is to go to your o2 server -> Data sources -> Custom -> Curl. Execute that curl command with `--trace -`, and copy the token from curl's output, it's the string after `Authorization: Basic`.

## UptimeKuma reporter
UptimeKume can be used as a reporter for jobs, though it is best suited as a heartbeat monitor. We show 3 use cases here, all assuming you have a push monitor at **endpoint url** `http://your_uptime_kuma_url/api/push/abCDeFG?status=up&msg=OK&ping=`.

#### Plain heartbeat monitor
Create a **get** endpoint and fill in the url. This reporter is now ready to be used as a simple heartbeat (for the jobs it is enabled for).

#### Set status
You can go a step further and have the monitor's status be determined by the job's exit code:
- set the **param name** to value `status`
- put this in your **template**: `{{ 'up' if exit_code == 0 else 'down'}}`

Because of setting the param name, the value of the parameter 'status' in your uptime kuma url is replaced with the exact output of your template.

#### Set status, msg and ping
Going even further, you can also set the msg and ping in your url, but to do this, we need to replace the whole url query:
- set **param name** to empty
- set the **template** to `status={{ 'up' if exit_code == 0 else 'down'}}&msg={{ message | truncate(300) | urlencode }}&ping={{duration}}`

Because the param name is empty, the template replaces the whole part in the url after the `?`.

## Readme reporter
A reporter that converts the report into markdown format and sends it as form data under parameter named 'summary':
- **method**: `post`
- **param name**: `summary`
- **template**:
  ```markdown
  # Report for {{name}}

  Mirrorr ran **{{name}}** and it all went {{ 'great' if exit_code == 0 else 'south'}}.

  ## File Stats
  Mirrorr transferred **{{human_readable_bytes_transferred}}**, created **{{created}}** new files and deleted **{{deleted}}** files. A total of **{{total_files}}** files.

  ## What happened
  Here's what Mirrorr has to say about what happened:

  {% if exit_code != 0 %}> I was running the job and then I got code {{exit_code}} and this message: {{ message | tojson }}. I had to report this and shout {{status}}!, but there was nothing more I could do.{% endif %}{% if exit_code == 0 %}> I was running the job and it was so nice and it completed with code {{exit_code}} and everything was great and I wanted to yell {{status}}, but anyway here's the message I received in the end: {{ message | tojson }}.{% endif %}

  This all happened {{ 'in environment ' ~ environment if environment else ''}} at {{report_timestamp_human_friendly}}. Took Mirrorr **{{human_readable_duration}}** to finish this off. Try also the [log file]({{logfile_url}})
  ```

## Discord reporter
A Discord webhook is ideal to be used as reporter, as it offers rich visual notifications. First get the url of a webhook from your Discord account, assuming thus an **endpoint url** `https://discord.com/api/webhooks/42678908/abCDeFG`. Discord requires a post endpoint that sends json data.
- **method**: post
- leave **param name** empty
- **template**: a valid discord webhook template like the following example

Below you can see an example that showcases **most** of the values made available via mirrorr):

```json
{
  "embeds": [
    {
      "title": "❗ {{status}} ❗",
      "url": "https://mirrorr.atyourdomain.com",
      "description": "Report for job **{{name}}**",
      "color": 15783023,
      "footer": {
        "text": "Date/timestamp: {{report_timestamp_human_friendly}}/({{report_timestamp}})\nSource: {{source}}\nDest: {{dest}}"
      },
      "fields": [
        {
          "name": "Exit code",
          "value": "{{exit_code}}"
        },
        {
          "name": "What Happened",
          "value": {{ ('Got this message: ' ~ message) | truncate(300) | tojson }}
        },
        {
          "name": "File Stats",
          "value": "Transferred: {{transferred}}, Created: {{created}},\nDeleted: {{deleted}}, Total: {{total_files}}"
        },
        {
          "name": "Bytes Transferred",
          "value": "{{human_readable_bytes_transferred}}"
        },
        {
          "name": "Took",
          "value": "{{human_readable_duration}}"
        },
        {
          "name": "Log",
          "value": "{{logfile_url}}"
        }
        {% if environment %}
         ,
        {
          "name": "Environment",
          "value": {{environment | tojson}}
        }
        {% endif %}
      ]
    }
  ]
}
```


## Escaping
Most placeholders used in a template are going to be replaced with values that are numbers. Those however that are strings may require json escaping, if the output of your template is json, or url encoding if a value is going in a url parameter.

Consider this line in your template:
```json
"value": "{{message}}"
```

If 'message' contains newlines or quotes or any other problematic character for json, it needs to be escaped. Escape json with `tojson`  and lose the surrounding quotes (Jinja will add them):
  ```json
  "value": {{message | tojson}}
  ```

  Similar to this, if your output needs to be url encoded, use `urlencode`.

#### More examples
Risky:
```json
"value": "Got this message: {{message}}"

"value": "Transferred: {{transferred}}, Created: {{created}}\nDeleted: {{deleted}}, Total: {{total_files}}"

msg={{message}}&status={{exit_code}}
```

Safe:
```json
"value": {{ ('Got this message: ' ~ message) | tojson}}

"value": {{ ('Transferred: ' ~ transferred ~ ', Created: ' ~ created ~ '\nDeleted: ' ~ deleted ~ ', Total: ' ~ total_files) | tojson }}

msg={{ message | truncate(300) | urlencode }}&status={{ exit_code | urlencode }}
```
Always check your logs for errors!  


## Conditionals
All Jinja conitional expressions are supported:
```json
{{ environment or 'No env set' }}

{{ environment if environment else 'No env set' }}

{% if environment %}...{% endif %}

{% if environment == 'myenvironment' %}...{% endif %}
```


