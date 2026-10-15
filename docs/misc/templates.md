# Templates

In this page you can find out how to make the most of using the templating engine in reporters and the heartbeat.

You can use a Jinja2 template to transform the job report or heartbeat json into any output you want. Care needs to be taken to not violate the content type of the request with invalid payloads. To troubleshoot your template, set the job you are testing with to debug mode, as this will print the payload before it is sent to the reporter or heartbeat endpoint. Errors are also logged to the standard output/error streams, see [logs](../setup.md#logs).

### Syntax
The standard Jinja2 syntax is used with 2 curly braces, an example of a text output:

```jinja
Hello, the job transferred {{bytes_transferred }} bytes
```
A json output:
```jinja
{
  "somename": "Hello, the job transferred {{bytes_transferred }} bytes"
}
```

All Jinja conditional expressions are supported:
```json
{{ environment or 'No env set' }}

{{ environment if environment else 'No env set' }}

{% if environment %}...{% endif %}

{% if environment == 'myenvironment' %}...{% endif %}
```

### Available placeholders for job reports
The available placeholders for templates processing **job report** payloads are shown [here](../configuration.md#job-report-payload).


### Escaping
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

#### More risky examples
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
