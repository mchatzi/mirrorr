async function fetchJobs() {
  try {
    const res = await fetch('/api/jobs');
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
    const urlEncodedJobName = encodeURIComponent(job.name);
    const jobEl = document.createElement("div");
    jobEl.className = "job-item";
    jobEl.innerHTML = `
      <div class="job-info">
        <h3>${job.name}</h3> 
        <p class="job-description">${job.description}</p>
        <p>
          <strong>Delete:</strong>&nbsp;${job.rsync_delete ? 'Delete' : 'No delete'}&nbsp;&nbsp;&nbsp;&nbsp;
          <strong>Schedule:</strong>&nbsp;${job.schedule}&nbsp;&nbsp;&nbsp;&nbsp;
          <strong>Allowed Percentage:</strong>&nbsp;${job.allowed_percentage}%
          ${job.running ? `<strong>running for:</strong>&nbsp;${job.runtime}` : 
            `<strong>last run:</strong>&nbsp;${job.lastrun}`}

          ${(job.rsync_no_owner || job.rsync_no_group || job.rsync_no_perms || job.rsync_acls || job.rsync_no_times ||
            job.rsync_in_place || job.rsync_whole_file || job.rsync_fsync || job.rsync_bwlimit ||
            job.rsync_nice || job.rsync_ionice || job.reporter_o2 || job.reporter_discord) ?
            "<br/>" : ""}

          ${job.rsync_no_owner ? '<strong class="rsync-active-option">no-owner</strong>' : ''}
          ${job.rsync_no_group ? '<strong class="rsync-active-option">no-group</strong>' : ''}
          ${job.rsync_no_perms ? '<strong class="rsync-active-option">no-perms</strong>' : ''}
          ${job.rsync_acls ? '<strong class="rsync-active-option">acls</strong>' : ''}
          ${job.rsync_no_times ? '<strong class="rsync-active-option">no-times</strong>' : ''}
          ${job.rsync_in_place ? '<strong class="rsync-active-option">in-place</strong>' : ''}
          ${job.rsync_whole_file ? '<strong class="rsync-active-option">whole-file</strong>' : ''}
          ${job.rsync_fsync ? '<strong class="rsync-active-option">fsync</strong>' : ''}

          ${job.rsync_bwlimit ? '<strong class="rsync-active-option">bwlimit: ' +
            ({ 2000000: "2GB/s", 1000000: "1GB/s", 500000: "500MB/s", 250000: "250MB/s", 100000: "100MB/s", 80000: "80MB/s", 
              60000: "60MB/s", 40000: "40MB/s", 30000: "30MB/s", 20000: "20MB/s", 10000: "10MB/s", 1000: "1MB/s", 100: "100KB/s" })
              [job.rsync_bwlimit] + '</strong>' : ''}

          ${job.rsync_nice ? '<strong class="rsync-active-option">Nice (' + job.rsync_nice + ')</strong>' : ''}
          ${job.rsync_ionice ? '<strong class="rsync-active-option">Ionice (' + job.rsync_ionice + ')</strong>' : ''}

          ${job.reporter_o2 ? '<strong class="rsync-active-option" title="Uses OpenObserve reporter">o2</strong>' : ''}
          ${job.reporter_discord ? '<strong class="rsync-active-option" title="Uses Discord reporter"><i class="bi bi-discord"></i></strong>' : ''}
        </p>
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

        ${job.logfile ? `<a href="joblog.html?name=${urlEncodedJobName}" class="logs-link" title="See logs">LOGS</a>` : ''}
        ${job.running ? `<label class="running-status" onclick="stopJobImmediately('${job.name}')" 
          title="Running now! Click to stop immediately" onmouseover="this.innerText='🚫'" onmouseleave="this.innerText='⚡⚡'">⚡⚡</label>` : ''}
      </div>`;

    jobEl.addEventListener('click', (event) => {
      // Prevent navigation when clicking on the toggle switch
      if (event.target.closest('.switch') || event.target.closest('input') ||
          event.target.closest('.running-status')) {
        return;
      }
      window.location.href = `job.html?name=${urlEncodedJobName}`;
    });

    container.appendChild(jobEl);
  });
}

async function toggleJobStatus(name, element) {
  //checkbox hasn't changed yet state
  enable = !element.target.checked ? false : true;

  try {
    const res = await fetch(`/api/jobs/${encodeURIComponent(name)}/toggle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ "enable": enable })
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
  }
}

async function stopJobImmediately(name) {
  if (!confirm(`Are you sure you want to kill job "${name}"?`))
    return;
  try {
    const res = await fetch(`/api/jobs/${encodeURIComponent(name)}/stop`, {
      method: "GET"
    });

    if (res.ok) {
      const status = await res.json();
      if (status['error']) {
        alert("Error stopping job: " + status['error']);
      } else {
        fetchJobs();
      }
    } else {
      alert("Error stopping job: " + res.status);
      console.error("Error stopping job: ", res.status);
    }
  } catch (err) {
    alert("Error stopping job: " + err);
    console.error("Error stopping job: ", err);
  }
}

async function toggleDryRuns(name, element) {
  //checkbox hasn't changed yet state
  enable = !element.target.checked ? false : true;

  try {
    const res = await fetch(`/api/jobs/${encodeURIComponent(name)}/dryruns`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ "enable": enable })
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
