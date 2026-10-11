# Configuring Mirrorr
The following can be configured under settings in the Mirrorr web interface.

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

Common use cases for reporters are for example an [OpenObserve](https://openobserve.ai/) instance, a [Discord webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks), an  [UptimeKuma](https://uptimekuma.org/) push monitor. You can find some elaborate examples of configuring these [here](misc/custom%20reporters.md).

### Configuration
Initially, fill in these options:
- **Name**: an identifiable name for this reporter
- **Endpoint url**: the url that can receive job events, e.g. `http://myserver:3300/?someparam=somevalue`
- **method**: the http method to use, either get or post.
- **headers**: any extra (to Content type) header you may want to send, e.g. `Basic Auth: cm9vdEBlyourGFtcGjareM7bh0u=m9vdEcrazi48fghj`. The Content type header is automatically set, see below.

Depending on the method, the options **param name** and **Template** are used very differently, read on.

#### Endpoints using method Get
When using Get urls, the report is communicated in the url query and no Content type header needs to be set. You have 2 options:
- Set **param name** to a value. Then a parameter with that name will be injected in your url and its value will be:
  - the full json report escaped and url encoded if you **don't** provide a Jinja  **Template**
  - exactly whatever your  **Template** outputs if you **do** provide one
- Leave the **param name** empty. Then:
  - if you **don't** provide a template, a parameter with name `report` is injected and the value is the report json, escaped and url encoded
  - if you **do** provide a template, then it acts as a **query** template: the whole part after `?` in your url will be replaced with the exact output of your template

#### Endpoints using method Post
For post endpoints, Mirrorr supports 2 types of payload, json or form data. This is determined by the **param name** option again:
- Leave the **param name** empty: the Content type will then be set to `application/json` and the body of the request is:
  - the report json _as is_, if you **don't** provide a template
  - exactly whatever your **Template** outputs if you **do** provide one (must be json!)
- Set the **param name** to a value: the Conten type is set to `application/x-www-form-urlencoded` and a parameter with that name is sent, with value:
  - the full json report escaped and url encoded if you **don't** provide a template
  - exactly whatever your **Template** outputs if you **do** provide one
 
#### Available placeholders
The available placeholders for templates processing job report payloads are: 

`name`, `source`, `dest` (string)  
`status` (SUCCESS, PARTIAL_SUCCESS, NOOP, INVALID, FAILED, UNKNOWN, KILLED, ABORTED)  
`environment` (string, needs escaping)   
`exit_code` (integer)  
`duration` (integer, seconds)  
`duration_human_readable`, `bytes_transferred_human_readable`, `report_timestamp_human_readable` (string)  
`bytes_transferred`, `created`, `deleted`, `transferred`, `total_files`, `allowed_percentage` (integer)  
`report_timestamp` (double)  
`logfile_url` (string, already url encoded + escaped)  
`message` (string, needs escaping, url encoding, truncating... )

See many examples of configuring endpoints [here](misc/custom%20reporters.md).


## Send Heartbeat
 Mirrorr can send send a request to a server upon every execution of a job. This is meant to be used in combination with a receiving end, e.g. a monitor application that supports push notifications, like [UptimeKuma](https://uptimekuma.org/). Then a monitor can be configured there to check, on a fixed interval, whether mirrorr jobs have executed. 
 
To enable this, fill in the "Heartbeat server" to the url of your service. For UptimeKuma this could be for example:
```
http://your_uptime_kuma_url/api/push/abCDeFG?status=up&msg=OK&ping=
```
Mirrorr will send a GET request to this url every time a job is completed, regardless of the job's completion status.

If using UptimeKuma, it's also possible to take into account the job status and also the reporters exit code. The status and msg of the push url can be affected by:
- the status of the completed job that is triggering the push. Jobs with a non 0 exit code will set the status to 'down'. To enable that, check **send job status** under the Send Heartbeat section. 
- the status of any reporters ran upon completion. Reporters with non 0 exit code will set the status to 'down'. To enable that, check **send reporters status** under the Send Heartbeat section. 

> If both "send job status" and "send reporters status" are set, the status is set to 'down' when either had a non 0 exit code.

> When either of these are set, your monitor in UptimeKuma will report 'down' on failed jobs or failed reporting, but this is ephemeral, as _any_ subsequent, and successful, job, will reset your monitor to up state again. Thus, using this feature as a _job status reporter_ is not as powerful as using a dedicated reporter _per job_. This is mostly meant to answer the question "_is mirrorr up and executing my jobs_".

## Remote SSH Port
When ssh shares are used, the port is asked for and registered during the installation process. This field shows that port and allows changing it in case you are configuring ssh keys manually. Changing this port always requires regenerating the `known_hosts` file that Mirrorr uses to establish ssh connections. See more on configuring ssh [here](setup.md#configuring-a-remote-ssh-share).

## Server Address
Reports sent to your reporters can contain a link to the job's log file (the variable `logfile_url`). The host used in that link can be specified here.

