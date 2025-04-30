const API_BASE = "http://192.168.2.201:5000"; // Update with your correct API URL

async function fetchJobs() {
  try {
    const res = await fetch(`${API_BASE}/api/jobs`);
    if (res.ok) {
      const jobs = await res.json();
      renderJobs(jobs);
    } else {
      document.getElementById("jobs-container").innerHTML = "Failed to load jobs";
      alert("Error loading jobs, status code:" + res.status);
      console.error("Error loading jobs, status code:" + res.status);
    }
  } catch (err) {
    document.getElementById("jobs-container").innerHTML = "Failed to load jobs";
    alert("Error loading jobs: " + err);
    console.error("Error loading jobs:", err);
  }
}

function renderJobs(jobs) {
  const container = document.getElementById("jobs-container");
  container.innerHTML = "";

  if (!jobs || jobs.length === 0) {
    container.innerHTML = "<p>No jobs found.</p>";
    return;
  }

  jobs.forEach(job => {
    const jobEl = document.createElement("div");
    jobEl.className = "job-item";
    jobEl.innerHTML = `
      <div class="job-info">
        <h3>${job.name}</h3> 
        <p class="job-description">${job.description}</p>
        <p><strong>Scope:</strong>&nbsp;${job.scope}&nbsp;&nbsp;&nbsp;&nbsp;<strong>Schedule:</strong>&nbsp;${job.schedule}&nbsp;&nbsp;&nbsp;&nbsp;<strong>Allowed Percentage:</strong>&nbsp;${job.allowed_percentage}%</p>
        <p class="from-to-label"><strong>From → To:</strong>&nbsp;&nbsp;<code>${job.source} → ${job.dest}</code></p>
      </div>
      <div class="job-sidebar">
        <label class="switch" title="${job.enabled ? 'Disable' : 'Enable'}">
          <input type="checkbox" ${job.enabled ? 'checked' : ''} onchange="toggleJobStatus('${job.name}', event)" />
          <span class="slider"></span>
        </label>
        <label title="${job.dryruns ? 'Run normally' : 'Run in dry mode'}">
          Dry
          <input type="checkbox" ${job.dryruns ? 'checked' : ''} onchange="toggleDryRuns('${job.name}', event)" />
        </label>

        ${job.logfile ? ('<a href="joblog.html?name=' + encodeURIComponent(job.name) + '" class="logs-link" title="See logs">LOGS</a>') : ''}
        ${job.running ? '<label class="running-status" title="Running now!">⚡</label>' : ''}
      </div>`;

    jobEl.addEventListener('click', (event) => {
      // Prevent navigation when clicking on the toggle switch
      if (event.target.closest('.switch') || event.target.closest('input')) {
        return;
      }
      window.location.href = `job.html?name=${encodeURIComponent(job.name)}`;
    });

    container.appendChild(jobEl);
  });
}

async function toggleJobStatus(name, element) {
  //checkbox hasn't changed yet state
  enable = !element.target.checked ? false : true;

  try {
    const res = await fetch(`${API_BASE}/api/jobs/${encodeURIComponent(name)}/toggle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ "enable" : enable })
    });

    if (res.ok) {
      const status = await res.json();
      if (status['error']) {
          alert("Error toggling job: " + status['error']);
      }
    } else {
      alert("Error toggling job: " + res.status);
      console.error("Error toggling job: ", res.status);      
    }

    fetchJobs();
  } catch (err) {
    alert("Error toggling job: " + err);
    console.error("Error toggling job: ", err);
    window.location.href = 'index.html';
  }
}

async function toggleDryRuns(name, element) {
  //checkbox hasn't changed yet state
  enable = !element.target.checked ? false : true;

  try {
    const res = await fetch(`${API_BASE}/api/jobs/${encodeURIComponent(name)}/dryruns`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ "enable" : enable })
    });

    if (res.ok) {
      const status = await res.json();
      if (status['error']) {
          alert("Error toggling dry runs: " + status['error']);
      }

    } else {
      alert("Error toggling dry runs: " + res.status);
      console.error("Error toggling dry runs: ", res.status);
    }
    fetchJobs();
  } catch (err) {
    alert("Error toggling dry runs: " + err);
    console.error("Error toggling dry runs: ", err);
    window.location.href = 'index.html';
  }
}

function autoreload(element) {
  autoreloadButton = element.target;
  enabled = autoreloadButton.hasAttribute("enabled");

  if (enabled) {
    clearInterval(INTERVAL_ID);
    autoreloadButton.removeAttribute("enabled");
    autoreloadButton.style.opacity = 0.4;
  } else {
    fetchJobs();
    INTERVAL_ID = setInterval(fetchJobs, 5000);
    autoreloadButton.setAttribute("enabled", true);
    autoreloadButton.style.opacity = 1;
  }  
}

fetchJobs();
