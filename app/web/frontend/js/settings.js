async function loadSettings() {
  try {
    const res = await fetch('/api/settings');
    if (res.ok) {
      const settings = await res.json();

      //Enable export button
      document.getElementById("settings-export-btn").href = `/data/settings`;
      document.getElementById("settings-export-btn").style.display = "inline-block";

      populateFormFromSettings(settings);
    } else if (res.status == 401) {
      window.location.reload();
      return;
    } else {
      alert("Error loading settings: " + res.status);
      console.error("Error loading settings:", res.status);
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
    "color_theme": form.theme.value.trim(),
    "reverse_cron": form.reverseCron.checked,

    "scheduler_cycle_s": form.schedulerCycleS.value,
    "ui_refresher_s": form.uiRefresherS.value,
    "log_retention_count": form.logRetentionCount.value,
    "your_brand": form.yourBrand.value,

    "o2_reporter": {
      "o2_server_url": form.o2ReporterServerUrl.value.trim(),
      "o2_server_auth": form.o2ReporterServerAuth.value.trim(),
    },
    "discord_reporter": {
      "webhook_url": form.discordReporterWebhookUrl.value.trim(),
      "template": form.discordReporterTemplate.value.trim(),
    },
    "health_heartbeat_url": form.healthHeartbeatUrl.value.trim(),
    "server_address": form.serverAddress.value.trim(),
    "remote_ssh_port": form.remoteSshPort.value.trim(),

  };
}

function populateFormFromSettings(settings) {
  document.getElementById("settings-color_theme").value = settings['color_theme'];
  document.getElementById("settings-reverse_cron").checked = 'reverse_cron' in settings ? settings['reverse_cron'] : true;
  document.querySelector(`input[name="schedulerCycleS"][value="${settings['scheduler_cycle_s']}"]`).checked = true;
  document.querySelector(`input[name="uiRefresherS"][value="${settings['ui_refresher_s']}"]`).checked = true;
  document.querySelector(`input[name="logRetentionCount"][value="${settings['log_retention_count']}"]`).checked = true;

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

  document.getElementById("settings-health_heartbeat_url").value = settings['health_heartbeat_url'] || "";
  document.getElementById("settings-server_address").value = settings['server_address'] || "";
  document.getElementById("settings-remote_ssh_port").value = settings['remote_ssh_port'] || "";
}

document.getElementById("settings-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const settings = createSettingsFromForm(form)

  try {
    const res = await fetch('/api/settings', {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });

    if (res.ok) {
    } else if (res.status == 401) {
      window.location.reload();
      return;
    } else {
      // TODO Validations went wrong perhaps etc
      alert("Something went wrong")
      console.error("Something went wrong")
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
    if (response.status == 401) {
      window.location.reload();
      return;
    } else if (!response.ok) {
      const error = await response.text();
      throw new Error(`${response.status}, ${error}`);
    } else {
      window.location.reload();
    }
  }).catch(error => {
    console.error('Error importing conf:', error);
    alert('Error importing conf:' + error.message);
  });
});


(function init() {
  loadSettings();
})();

