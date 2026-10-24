# Heartbeats

Configuring the heartbeat is explained [here](../configuration.md#send-heartbeat). In this page you can find a few implementations for some major platforms.


### **UptimeKuma heartbeat**
UptimeKuma is ideal as a heartbeat receiver, as it supports push monitors out of the box. Assuming you have a push monitor at **endpoint url** `http://your_uptime_kuma_url/api/push/abCDeFG?status=up&msg=OK&ping=`, to make a simple heartbeat all you need to do is create a **get** endpoint and fill in this url. Mirrorr will request that url on every job completion.

You can change the status, msg and ping parameters (by using a template), but then this becomes a job reporter rather than a heartbeat. This is actually covered [here](reporters.md#uptimekuma-reporter) but to apply that approach using a heartbeat payload (very different than a job payload) adjust the placeholders in the template: instead of `exit_code` you will need to use `last_job_exit_code` and instead of `name` use `last_job_name`.  

But note that a heartbeat is mostly useful for other types of monitors, like, monitoring if the percentage of successful vs failed jobs falls under some threshold, see [this example](statistics.md#home-assistant).


### **Home Assistant heartbeat**
Go to Settings → Automations & scenes → Create automation → Create new automation → Edit in YAML and paste this:

```yaml
alias: Mirrorr Heartbeat
description: Sends notification when Mirrorr sends heartbeat
triggers:
  - trigger: webhook
    webhook_id: REPLACE_WITH_A_LONG_RANDOM_SECRET
    allowed_methods:
      - POST
    local_only: true
actions:
  - action: persistent_notification.create
    data:
      title: Mirrorr Heartbeat
      message: |
        Mirrorr status: {{ trigger.query.get('status', 'unknown') }}
mode: single
```

Then go to Mirrorr settings and set the heartbeat to:  
- **endpoint**: `http://yourhomeassistant:8123/api/webhook/REPLACE_WITH_A_LONG_RANDOM_SECRET?status=up`  
- **method**: `post`

Home Assistant can also be used as a reporter for jobs, see [here](reporters.md#home-assistant-reporter), and as a [consumer for the stats api](statistics.md#home-assistant).