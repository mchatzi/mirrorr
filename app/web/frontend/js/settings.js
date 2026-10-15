async function loadSettings() {
  try {
    const response = await fetch('/api/settings');
    if (response.ok) {
      const settings = await response.json();

      //Enable export button
      document.getElementById("settings-export-btn").href = `/data/settings`;
      document.getElementById("settings-export-btn").style.display = "inline-block";

      populateFormFromSettings(settings);
    } else if (response.status == 401) {
      window.location.reload();
      return;
    } else {
      alert("Error loading settings: " + response.status);
      console.error("Error loading settings:", response.status);
    }
  } catch (err) {
    alert("Error loading settings: " + err)
    console.error("Error loading settings:", err);
  }
}

function autoResize(textarea) {
  const scrollY = window.scrollY;
  textarea.style.height = 'auto';
  textarea.style.height = textarea.scrollHeight + 'px';
  window.scrollTo({ top: scrollY });
}

function createSettingsFromForm(form) {
  return {
    "color_theme": form.color_theme.value,
    "reverse_cron": form.reverse_cron.checked,
    "cool_timestamps": form.cool_timestamps.checked,

    "scheduler_cycle_s": form.scheduler_cycle_s.value == "" ? null : parseInt(form.scheduler_cycle_s.value, 10),
    "ui_refresher_s": form.ui_refresher_s.value == "" ? null : parseInt(form.ui_refresher_s.value, 10),
    "environment": form.environment.value,

    "reporters": getReportersFromForm()
    ,
    "heartbeat": {
      "health_heartbeat_url": form.health_heartbeat_url.value.trim(),
      "send_job_status": form.send_job_status.checked,
      "send_reporters_status": form.send_reporters_status.checked
    },
    "server_address": form.server_address.value.trim(),
    "remote_ssh_port": form.remote_ssh_port.value == "" ? null : form.remote_ssh_port.valueAsNumber,
  };
}

function populateFormFromSettings(settings) {
  document.getElementById("settings-color_theme").value = settings['color_theme'];
  document.getElementById("settings-reverse_cron").checked = 'reverse_cron' in settings ? settings['reverse_cron'] : true;
  document.getElementById("settings-cool_timestamps").checked = 'cool_timestamps' in settings ? settings['cool_timestamps'] : true;
  document.querySelector(`input[name="scheduler_cycle_s"][value="${settings['scheduler_cycle_s']}"]`).checked = true;
  document.querySelector(`input[name="ui_refresher_s"][value="${settings['ui_refresher_s']}"]`).checked = true;
  document.getElementById("settings-environment").value = settings['environment'] || "";
  
  if ('reporters' in settings) {
    for (const reporter of settings['reporters']) {
      addReporter(reporter);
    }
  }
  
  if (settings['heartbeat']) {
    document.getElementById("settings-health_heartbeat_url").value = settings['heartbeat']['health_heartbeat_url'] || "";
    document.getElementById("settings-send_job_status").checked = 'send_job_status' in settings['heartbeat'] ? settings['heartbeat']['send_job_status'] : false;
    document.getElementById("settings-send_reporters_status").checked = 'send_reporters_status' in settings['heartbeat'] ? settings['heartbeat']['send_reporters_status'] : false;
  }

  document.getElementById("settings-server_address").value = settings['server_address'] || "";
  document.getElementById("settings-remote_ssh_port").value = settings['remote_ssh_port'] || "";
}

document.getElementById("settings-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const settings = createSettingsFromForm(form)

  document.getElementById("save-status").style.visibility = "hidden";

  try {
    const response = await fetch('/api/settings', {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });

    if (response.ok) {
      document.getElementById("save-status").style.visibility = "visible";
    } else if (response.status == 401) {
      window.location.reload();
      return;
    } else if (response.status == 400) { 
      const responseJson = await response.json();
      const errors = [];
      responseJson.validation.forEach(violation => {
        const fieldName = Object.keys(violation)[0];
        const violationMsg = violation[fieldName];
        errors.push((fieldName == "general" ? "" : (fieldName + ": ")) + violationMsg);        
      });
      const errMsg = "Validation error(s): \n" + errors.join("\n");
      alert(errMsg);
      console.error(errMsg);
    } else {
      const error = await response.text();
      throw new Error(`${response.status}, ${error}`);
    }
  } catch (err) {
    alert("Error saving settings: " + err)
    console.error("Error saving settings:", err);
  }
});

document.getElementById("settings-import-btn").addEventListener('click', (e) => {
  e.preventDefault();
  document.getElementById("settings-import-file").click();
});


document.getElementById("settings-import-file").addEventListener('change', async (e) => {
  const fileInput = e.target;
  const file = fileInput.files[0];
  if (!file) {
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  fetch("/data/settings", {
    method: 'POST',
    body: formData
  }).then(async (response) => {
    if ([200, 201, 401].includes(response.status)) {
      window.location.reload();
      return;
    } else if (response.status == 400) { 
      const responseJson = await response.json();
      const errors = [];
      responseJson.validation.forEach(violation => {
        const fieldName = Object.keys(violation)[0];
        const violationMsg = violation[fieldName];
        errors.push((fieldName == "general" ? "" : (fieldName + ": ")) + violationMsg);        
      });
      const errMsg = "Validation error(s): \n" + errors.join("\n");
      alert(errMsg);
      console.error(errMsg);
    } else {
      const error = await response.text();
      throw new Error(`${response.status}, ${error}`);
    }
  }).catch(error => {
    console.error('Error importing conf:', error);
    alert('Error importing conf:' + error.message);
  });
});


function addReporter(reporter) {
    const reporterSpan = document.querySelector('span.reporter-box[hidden]');
    const newReporterSpan = reporterSpan.cloneNode(true);

    const nameEL = newReporterSpan.querySelector("input.reporter_name")
    nameEL.setAttribute("required", true);

    const endpointEl = newReporterSpan.querySelector("input.reporter_endpoint");
    endpointEl.setAttribute("required", true);

    const templateHelperEl = newReporterSpan.querySelector("span.reporter_template_helper");
    const methodEl = newReporterSpan.querySelector("select.reporter_method");
    const parameterNameEl = newReporterSpan.querySelector("input.reporter_parameter_name");

    const autoTemplateHelper = () => {
      const paramNameValue = parameterNameEl.value;
      templateHelperEl.innerText = methodEl.value == "GET" ?
        paramNameValue == "" ? "(replaces url query)" : `(sets parameter '${paramNameValue}')` : 
        paramNameValue == "" ? "(replaces json payload)" : `(sets form data parameter '${paramNameValue}')`;
    };
    methodEl.addEventListener('change', autoTemplateHelper);
    parameterNameEl.addEventListener('input', autoTemplateHelper);

    const templateEl = newReporterSpan.querySelector("textarea.reporter_template");
    templateEl.addEventListener('input', (e) => autoResize(e.target));

    if (reporter) {
        if ("name" in reporter) {
            nameEL.value = reporter["name"] || "";
        }
        if ("endpoint" in reporter) {
            endpointEl.value = reporter["endpoint"] || "";
        }
        if ("method" in reporter) {
            methodEl.value = reporter["method"] || "GET";
        }
        if ("parameter_name" in reporter) {
            parameterNameEl.value = reporter["parameter_name"] || "";
        }
        if ("headers" in reporter) {
            newReporterSpan.querySelector("input.reporter_headers").value = reporter["headers"] || "";
        }
        if ("template" in reporter) {          
            templateEl.value = reporter["template"] || "";
        }
    }

    newReporterSpan.style.display = 'block';
    newReporterSpan.removeAttribute("hidden");
    document.getElementById("create-reporter-button").before(newReporterSpan);
    
    autoTemplateHelper();
    autoResize(templateEl);
}


function deleteReporter(deleteButton) {
    if (confirm("Are you sure you want to delete this reporter?")) {
        deleteButton.parentElement.remove();
    }
}


function getReportersFromForm() {
    const reporters = [];
    document.querySelectorAll('span.reporter-box:not([hidden])').forEach(reporterSpan => {
        reporters.push(getReporterFromForm(reporterSpan));
    });
    return reporters;
}


function getReporterFromForm(reporterSpan) {
    return {
        "name": reporterSpan.querySelector("input.reporter_name").value,
        "endpoint": reporterSpan.querySelector("input.reporter_endpoint").value,
        "method":reporterSpan.querySelector("select.reporter_method").value,
        "parameter_name": reporterSpan.querySelector("input.reporter_parameter_name").value,
        "headers": reporterSpan.querySelector("input.reporter_headers").value,
        "template": reporterSpan.querySelector("textarea.reporter_template").value
    };
}

(function init() {
  loadSettings();
})();

