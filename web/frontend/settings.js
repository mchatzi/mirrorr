const API_BASE = "http://192.168.2.201:5000";

async function loadSettings() {
  try {
    const res = await fetch(`${API_BASE}/api/settings`);
    if (res.ok) {
      const settings = await res.json();
      document.getElementById("settings-color-theme").value = settings['color-theme'];
      document.getElementById("settings-o2reporter-o2server-url").value = settings['o2reporter']['o2server-url'];
      document.getElementById("settings-o2reporter-o2server-auth").value = settings['o2reporter']['o2server-auth'];
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
    "color-theme": form.theme.value.trim(),
    "o2reporter": {
      "o2server-url": form.o2reporterServerUrl.value.trim(),
      "o2server-auth": form.o2reporterServerAuth.value.trim(),
    }
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

