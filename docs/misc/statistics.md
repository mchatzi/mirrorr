# Statistics

Mirrorr keeps statistics, available for your dashboard at `/api/stats`. Mirrorr counts the number of jobs it has run, the total duration, total bytes transferred and much more. A sample json output can be seen below:

```json
{
  "environment": "Machine 2",
  "last_job_exit_code": 0,
  "last_job_name": "Copy the pictures to storage 2",
  "last_reporters_exit_code": 0,
  "last_updated_at": 1791883540.50219,
  "last_updated_at_human_readable": "2026-10-13 11:25:40",
  "number_of_jobs": "7/2",
  "status": "up",
  "total_bytes_transferred": 531688157189,
  "total_bytes_transferred_human_readable": "495.17GB",
  "total_executions": 7527,
  "total_executions_duration": 178461,
  "total_executions_duration_human_readable": "2d1h",
  "total_executions_human_readable": "7.5K",
  "total_fails": 135,
  "total_noops": 5507,
  "total_reporters_fails": 8,
  "total_successes": 1885,
  "uptime": 794624.67655801773,
  "uptime_human_readable": "9d4h43m45s",
  "version": "0.7.0-alpha"
}
```

#### _Stats behind login_
If you have [logins enabled](../setup.md#logins), you will need to authenticate, which is easy if you're integrating with a dashboard but trickier if using a browser. Easiest is to log in to the Mirrorr app in a new tab in your browser. Otherwise you need to pass the `Authorization` header, which can be done with a header modification browser extension. For the default admin/password credentials, the header value would be `Basic YWRtaW46cGFzc3dvcmQ=`



## Dashboard integrations

### **Homepage**
Creating a widget for [Homepage](https://gethomepage.dev/) dashboard is incredibly easy:

```yaml
- Mirrorr:
    href:  http://mymirrorr:5000/
    icon: http://mymirrorr:5000/favicon.ico
    widget:
      type: customapi
        url:  http://mymirrorr:5000/api/stats
        refreshInterval: 10000
        
        # Username and password if logins enabled
        #username: username
        #password: password

        mappings:
          - label: Jobs
            field: number_of_jobs
          - label: Data
            field: total_bytes_transferred_human_readable
          - label: Runs
            field: total_executions_human_readable
          - label: Time
            field: total_executions_duration_human_readable

        #   - label: Uptime
        #     field: uptime_human_readable
        #   - label: Ok ✔️
        #     field: total_successes
        #     format: number
        #   - label: No-ops
        #     field: total_noops
        #     format: number
        #   - label: Not Ok ❌
        #     field: total_fails
        #     format: number
```



### **Dashy**
Creating a widget for [Dashy](https://dashy.to/) dashboard is equally easy:

```yaml
  - name: Mirrorr
    icon: fas fa-chart-line
    widgets:
      - type: customapi
        options:
          url: http://mymirrorr:5000/api/stats
          refreshInterval: 20000

        # Username and password if logins enabled

        # REQUIRES 
        # useProxy: true

        # username: 
        # password: 

          mappings:
            - label: 'Environment'
              field: 'environment'
            - label: 'Uptime'
              field: 'uptime_human_readable'
            - label: 'Version'
              field: 'version'
            - label: 'Last exit code'
              field: 'last_job_exit_code'
              format: number
            - label: 'Last job name'
              field: 'last_job_name'
            - label: 'Last reporters exit code'
              field: 'last_reporters_exit_code'
              format: number
            - label: 'Statistics updated at'
              field: 'last_updated_at_human_readable'
            - label: 'Number of jobs (enbaled/disabled)'
              field: 'number_of_jobs'
            - label: 'Total data transferred'
              field: 'total_bytes_transferred_human_readable'
            - label: 'Total runs'
              field: 'total_executions_human_readable'
            - label: 'Total execution runtime'
              field: 'total_executions_duration_human_readable'
            - label: 'Total successess'
              field: 'total_successes'
              format: number
            - label: 'Total noops'
              field: 'total_noops'
              format: number
            - label: 'Total fails'
              field: 'total_fails'
              format: number
            - label: 'Total reporter fails'
              field: 'total_reporters_fails'
```


### **Home Assistant**
Consuming the api from [HomeAssistant](https://www.home-assistant.io/) is incredibly easy. Below is a simle rest endpoint with a sensor that plots the total number of executions and also exposes some attributes for use in other value templates.


```yaml
rest:
  - authentication: basic
    username: "admin"
    password: "password"
    scan_interval: 20
    resource: http://10.36.10.208:5000/api/stats
    sensor:
      - name: "Mirrorr Stats"
        value_template: "{{ value_json.total_successes }}"
        state_class: total_increasing
        json_attributes_path: "$"
        json_attributes:
          - "total_successes"
          - "total_executions"
          - "total_noops"
```

You can then use the attributes exposed from your sensor in other sensors, this one for example monitors the percentage of successful jobs against the total number of jobs:

```yaml
template:
  - sensor:
      - name: "Mirrorr Success Percentage"
        unique_id: mirrorr_success_percentage
        state: >
          {% set successes = state_attr('sensor.mirrorr_stats', 'total_successes') | int(0) %}
          {% set noops = state_attr('sensor.mirrorr_stats', 'total_noops') | int(0) %}
          {% set total = state_attr('sensor.mirrorr_stats', 'total_executions') | int(0) %}
          {{ ((successes + noops) / total * 100) | round(2) if total > 0 else 0 }}
        unit_of_measurement: "%"
        state_class: measurement
```

Home Assistant can also be used as a reporter for jobs, see [here](reporters.md#home-assistant-reporter), and as a heartbeat, see [here](heartbeats.md#uptimekuma-heartbeat).