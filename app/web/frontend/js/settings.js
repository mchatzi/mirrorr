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
    "color_theme": form.color_theme.value.trim(),
    "reverse_cron": form.reverse_cron.checked,
    "cool_timestamps": form.cool_timestamps.checked,

    "scheduler_cycle_s": form.scheduler_cycle_s.value == "" ? null : parseInt(form.scheduler_cycle_s.value, 10),
    "ui_refresher_s": form.ui_refresher_s.value == "" ? null : parseInt(form.ui_refresher_s.value, 10),
    "log_retention_count": form.log_retention_count.value == "" ? null : parseInt(form.log_retention_count.value, 10),
    "your_brand": form.your_brand.value,

    "o2_reporter": {
      "o2_server_url": form.o2_reporter_o2_server_url.value.trim(),
      "o2_server_auth": form.o2_reporter_o2_server_auth.value.trim(),
    },
    "discord_reporter": {
      "webhook_url": form.discord_reporter_webhook_url.value.trim(),
      "template": form.discord_reporter_template.value.trim(),
    },
    "heartbeat": {
      "health_heartbeat_url": form.health_heartbeat_url.value.trim(),
      "send_job_status": form.send_job_status.checked
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
  document.querySelector(`input[name="log_retention_count"][value="${settings['log_retention_count']}"]`).checked = true;

  document.getElementById("settings-your_brand").value = settings['your_brand'] || "";
  
  if (settings['o2_reporter']) {
    document.getElementById("settings-o2_reporter_o2_server_url").value = settings['o2_reporter']['o2_server_url'] || "";
    document.getElementById("settings-o2_reporter_o2_server_auth").value = settings['o2_reporter']['o2_server_auth'] || "";
  }

  if (settings['discord_reporter']) {
    document.getElementById("settings-discord_reporter_webhook_url").value = settings['discord_reporter']['webhook_url'] || "";
    document.getElementById("settings-discord_reporter_template").value = settings['discord_reporter']['template'] || "";
    autoResize(document.getElementById("settings-discord_reporter_template"))
  }

  if (settings['heartbeat']) {
    document.getElementById("settings-health_heartbeat_url").value = settings['heartbeat']['health_heartbeat_url'] || "";
    document.getElementById("settings-send_job_status").checked = 'send_job_status' in settings['heartbeat'] ? settings['heartbeat']['send_job_status'] : false;
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


document.getElementById("settings-discord_reporter_template")
  .addEventListener('input', (e) => autoResize(e.target));


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


(function init() {
  loadSettings();
})();

