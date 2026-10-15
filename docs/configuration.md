# Configuring Mirrorr
The following can be configured under settings in the Mirrorr web interface, see also [screenshot](screenshots/settings%20page.png).

## Appearance

- **theme**: a set of themes to customize your installation
- **reverse cron**: show cron schedules reversed in the home page job listing. For better readability

## Timings
Here you can configure:
- the **Scheduler cycle**: how often the scheduler checks whether any jobs  need running. Defaults to 1 minute.
- the **Refresh UI** frequency: how often the job list in the homepage auto-refreshes (when autoreload is enabled)

## Environment
If you are running different Mirrorr instances in multiple environments, use this as an identifier to help you distinguish both UI, logs and reports between those environments. The environment is sent and recorded in all jobs logs and reports, and it is also rendered next to the Mirrorr logo in the UI.

## Reporters
Job reporters are url endpoints that Mirrorr notifies upon completions of jobs. Both get and post based endpoints are supported, and all the job status information is available as either json or as dictated by a user provided [Jinja](https://jinja.palletsprojects.com/en/stable/) template. Reports are run at the end of a job and before the [heartbeat](#send-heartbeat) is sent. 

Common use cases for reporters are for example an [OpenObserve](https://openobserve.ai/) instance, a [Discord webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks), a [HomeAssistant](https://www.home-assistant.io/) instance, an [UptimeKuma](https://uptimekuma.org/) push monitor. You can find elaborate examples of configuring these [here](misc/reporters.md#reporter-integrations).

### Configuration
Initially, fill in these options:
- **Name**: an identifiable name for this reporter
- **Endpoint url**: the url that can receive job events, e.g. `http://myserver:3300/?someparam=somevalue`
- **method**: the http method to use, either get or post.
- **headers**: any extra (to Content type) header you may want to send, e.g. `Basic Auth: cm9vdEBlyourGFtcGjareM7bh0u=m9vdEcrazi48fghj`. The Content type header is automatically set, see below.

The rest of the options, **param name** and **Template**, are used very differently depending on the method used:

#### _Endpoints using method Get_
When using Get urls, the report payload can only be communicated in the url query. No Content type header needs to be set. You have 2 options:
- Set **param name** to a value. Then a parameter with that name will be injected in your url query and its value will be:
  - the full json report escaped and url encoded, if you **don't** provide a Jinja  **Template**
  - exactly whatever your  **Template** outputs if you **do** provide one
- Leave the **param name** empty. Then:
  - if you **don't** provide a template, then no payload is transmitted at all. Your endpoint url gets called as is
  - if you **do** provide a template, then it acts as a **query** template: the whole part after `?` in your url will be replaced with the exact output of your template

#### _Endpoints using method Post_
For post endpoints, Mirrorr always sends the payload and it supports 2 content types for doing this: json or form data. This is determined by the **param name** option:
- Leave the **param name** empty: the Content type will then be set to `application/json` and the body of the request is:
  - the report json _as is_, if you **don't** provide a template
  - exactly whatever your **Template** outputs if you **do** provide one (must be json!)
- Set the **param name** to a value: the Content type will be set to `application/x-www-form-urlencoded` and a parameter with that name is sent, with value:
  - the full json report escaped and url encoded if you **don't** provide a template
  - exactly whatever your **Template** outputs if you **do** provide one

### Job report payload
The (json) payload for job reports contains the information seen below. These are also the available placeholders in case you are using a template, with a hint when a value needs to be escaped (template output is transmitted as is, so make sure you escape strings).

`name`, `source`, `dest` (string)  
`status` (string enum -> "SUCCESS", "PARTIAL_SUCCESS", "NOOP", "INVALID", "FAILED", "UNKNOWN", "KILLED", "ABORTED")  
`environment` (string, needs escaping)   
`exit_code`, `bytes_transferred`, `created`, `deleted`, `transferred`, `total_files`, `allowed_percentage` (integer)  
`duration` (integer, seconds)  
`duration_human_readable`, `bytes_transferred_human_readable`, `report_timestamp_human_readable` (string)  
`report_timestamp` (double, timestamp)  
`logfile_url` (string, already url encoded + escaped)  
`message` (string, needs escaping, url encoding, truncating... )

### Templates
See details on writing templates [here](misc/templates.md).


## Send Heartbeat
At the very end of a job execution, Mirrorr can send a request to a server to notify that it is alive and executing jobs. The request is sent regardless of the job's completion status, and a job cannot opt-out of this notification. This is meant to be used in combination with a monitoring service, e.g. [UptimeKuma](https://uptimekuma.org/). Then a monitor can be configured on the remote side to check, on a fixed interval, whether Mirrorr has been sending heartbeats and thus whether it's executing jobs.

To enable the heartbeat, fill in the "Heartbeat endpoint" to a url (and optionally configure the rest of the options).

The heartbeat can be [configured like any other reporter](#configuration), but it has access to, and optionally transmits, a very different payload than a job reporter. Specifically, it can trasmit overview data and statistics for the app's overall health, rather than for particular jobs.

See example heartbeats with some major services [here](misc/heartbeats.md).

### Heartbeat payload
The (json) payload for heartbeats contains the information seen below. These are also the available placeholders in case you are using a template for the heartbeat, with a hint when a value needs to be escaped (template output is transmitted as is, so make sure you escape strings).

`status` (string enum -> "up" | "down")  
`environment` (string, needs escaping)  
`total_executions`, `total_executions_duration`, `total_bytes_transferred`, `total_noops`, `total_successes`, `total_fails`, `total_reporters_fails`, `last_reporters_exit_code`, `last_job_exit_code` (integer)  
`total_executions_duration` (integer, seconds)   
`version`, `total_executions_human_readable`, `total_executions_duration_human_readable`, `heartbeat_timestamp_human_readable`, 
`total_bytes_transferred_human_readable`, `last_job_name`, `last_updated_at_human_readable` (string)  
`heartbeat_timestamp`, `last_updated_at` (double, timestamp)  

### Templates
See details on writing templates [here](misc/templates.md).


## Remote SSH Port
When ssh shares are used, the port is asked for and registered during the installation process. This field shows that port and allows changing it in case you are configuring ssh keys manually. Changing this port always requires regenerating the `known_hosts` file that Mirrorr uses to establish ssh connections. See more on configuring ssh [here](setup.md#configuring-a-remote-ssh-share).

## Server Address
Reports sent to your reporters can contain a link to the job's log file (the variable `logfile_url`). The host used in that link can be specified here.

