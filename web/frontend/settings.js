const API_BASE = "http://192.168.2.201:5000";

async function loadSettings() {
  try {
    const res = await fetch(`${API_BASE}/api/settings`);
    if (res.ok) {
      const settings = await res.json();
      document.getElementById("settings-color_theme").value = settings['color_theme'];

      if (settings['o2_reporter']) {
        document.getElementById("settings-o2_reporter_o2server_url").value = settings['o2_reporter']['o2_server_url'] || "";
        document.getElementById("settings-o2_reporter_o2server_auth").value = settings['o2_reporter']['o2_server_auth'] || "";
      }

      document.getElementById("settings-health_listener").value = settings['health_listener'] || "";
    } else {
      alert("Error loading settings: " + res.status);
      console.error("Error loading settings:", res.status);
    }
  } catch (err) {
    alert("Error loading settings: " + err)
    console.error("Error loading settings:", err);
  }
}

document.getElementById("settings-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const settings = {
    "color_theme": form.theme.value.trim(),
    "o2_reporter": {
      "o2_server_url": form.o2reporterServerUrl.value.trim(),
      "o2_server_auth": form.o2reporterServerAuth.value.trim(),
    },
    "health_listener": form.healthListener.value.trim(),
  };

  try {
    const res = await fetch(`${API_BASE}/api/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });

    if (res.ok) {
      window.location.reload();
    } else {
      // TODO Validations went wrong perhaps etc
      alert("Something went wrong")
    }
  } catch (err) {
    alert("Error saving settings: " + err)
    console.error("Error saving settings:", err);
  }
});

loadSettings();

