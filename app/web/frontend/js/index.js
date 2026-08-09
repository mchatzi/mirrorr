async function fetchJobs() {
  try {
    const res = await fetch('/api/jobs');
    if (res.ok) {
      const jobs = await res.json();
      renderJobs(jobs);
    } else if (res.status == 401) {
      window.location.reload();
      return;
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

  updateDebugModes(jobs)

  const unfilteredJobsLength = jobs.length;
  filterJobs(jobs, document.getElementById("filter-options").getAttribute("filter-by"));

  updateStatusCounters(jobs, 
    isFiltered = jobs.length != unfilteredJobsLength);
  
  sortJobs(jobs, 
    document.getElementById("sort-options").getAttribute("sort-by"), 
    document.getElementById("sort-options").getAttribute("sort-order"));

  jobs.forEach(job => {
    const urlEncodedJobName = encodeURIComponent(job.name);
    const next_run_str = job.next_run ? printDurationFromNow(job.next_run, false) : null;

    const jobEl = document.createElement("div");
    jobEl.className = "job-item";
    jobEl.innerHTML = `
      <div class="job-info">
        <h3>${job.name}</h3>
        <p class="job-description">${job.description}</p>
        <p>
          <strong>Schedule:</strong>&nbsp;${job.schedule}&nbsp;&nbsp;&nbsp;&nbsp;
          ${ (job.rsync_delete && job.allowed_percentage) ? `<strong>Allowed Percentage:</strong>&nbsp;${job.allowed_percentage}%&nbsp;&nbsp;&nbsp;&nbsp;` : ''}
          ${(job.status == 'running' ? `<strong>Running for:</strong>&nbsp;${job.started_at ? printDurationToNow(job.started_at, false) : 'no info'}` :
            `<strong>Last run:</strong>&nbsp;${job.last_run ? printDurationToNow(job.last_run, false) + ' ago' : 'Never'}`)}&nbsp;&nbsp;&nbsp;&nbsp

          ${job.status != 'running' && next_run_str ? 
            (next_run_str[0] == '-' ?
              `<strong>Queued:</strong>&nbsp;${next_run_str.substring(1)}` :
              `<strong>Next run:</strong>&nbsp;${next_run_str}`) : '' }

          ${(job.rsync_no_owner || job.rsync_no_group || job.rsync_no_perms || job.rsync_acls || job.rsync_no_times ||
            job.rsync_in_place || job.rsync_whole_file || job.rsync_fsync || job.rsync_bwlimit || job.rsync_delete ||
            job.rsync_nice || job.rsync_ionice || job.reporter_o2 || job.reporter_discord || job.debug) ?
            "<br/>" : ""}

          ${job.rsync_no_owner ? '<strong class="rsync-active-option" title="Will not try to change ownership to folders and files on destination">no-owner</strong>' : ''}
          ${job.rsync_no_group ? '<strong class="rsync-active-option" title="Will not try to change groups to folders and files on destination">no-group</strong>' : ''}
          ${job.rsync_no_perms ? '<strong class="rsync-active-option" title="Will not try to change permissions to folders and files on destination">no-perms</strong>' : ''}
          ${job.rsync_acls ? '<strong class="rsync-active-option" title="Will apply acls to folders and files on destination">acls</strong>' : ''}
          ${job.rsync_no_times ? '<strong class="rsync-active-option" title="Will not try to set times on folders and files on destination">no-times</strong>' : ''}
          ${job.rsync_in_place ? '<strong class="rsync-active-option" title="Will not create temporary files on destination">in-place</strong>' : ''}
          ${job.rsync_whole_file ? '<strong class="rsync-active-option" title="Will not do delta transfers; it always send whole file">whole-file</strong>' : ''}
          ${job.rsync_fsync ? '<strong class="rsync-active-option" title="Will use fsync and try flushing data immediately to destination">fsync</strong>' : ''}

          ${job.rsync_bwlimit ? '<strong class="rsync-active-option" title="Limit the trasnfer speed">bwlimit: ' +
            ({ 2000000: "2GB/s", 1000000: "1GB/s", 500000: "500MB/s", 250000: "250MB/s", 100000: "100MB/s", 80000: "80MB/s",
              60000: "60MB/s", 40000: "40MB/s", 30000: "30MB/s", 20000: "20MB/s", 10000: "10MB/s", 1000: "1MB/s", 100: "100KB/s" })
              [job.rsync_bwlimit] + '</strong>' : ''}

          ${job.rsync_delete ? '<strong class="rsync-active-option" title="Will perform deletions on destination">delete</strong>' : ''}
          ${job.rsync_nice ? '<strong class="rsync-active-option" title="Will use nice in front of rsync">Nice (' + job.rsync_nice + ')</strong>' : ''}
          ${job.rsync_ionice ? '<strong class="rsync-active-option" title="How much nice should it be">Ionice (' + job.rsync_ionice + ')</strong>' : ''}

          ${job.reporter_o2 ? '<strong class="rsync-active-option" title="Uses OpenObserve reporter">o2</strong>' : ''}
          ${job.reporter_discord ? '<strong class="rsync-active-option" title="Uses Discord reporter"><i class="bi bi-discord"></i></strong>' : ''}
          ${job.debug ? '<strong class="rsync-active-option" title="Is in debug mode"><i style="color:#4a4aeb" class="bi bi-bug"></i></strong>' : ''}
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
        ${job.status == 'running' ? `<label class="running-status" onclick="stopJobImmediately('${job.name}')"
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

function updateStatusCounters(jobs, isFiltered) {
  const enabledCount = jobs.filter(job => job.enabled).length;
  const disabledCount = jobs.filter(job => job.enabled == false).length;
  document.getElementById("status-counters").innerHTML = 
    `(<span class="job-counter-enabled">${enabledCount}</span>/<span class="job-counter-disabled">${disabledCount}</span>)
      ${ isFiltered ? ' (<i class="bi bi-funnel-fill"></i>)' : ''}`;
}

function updateDebugModes(jobs) {
  const jobInDebugMode = jobs.filter(job => job.debug && job.enabled).length != 0;
  document.querySelector("#job-in-debug-mode").style.display = jobInDebugMode ? 'block' : 'none';
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
        console.error("Error toggling job: " + status['error']);
      }
    } else if (res.status == 401) {
      window.location.reload();
      return;
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
        console.error("Error stopping job: " + status['error']);
      } else {
        fetchJobs();
      }
    } else if (res.status == 401) {
      window.location.reload();
      return;
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
  const enable = !element.target.checked ? false : true;

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
        console.error("Error toggling dry runs: " + status['error']);
      }
    } else if (res.status == 401) {
      window.location.reload();
      return;
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
    INTERVAL_ID = setInterval(fetchJobs, UI_REFRESH_IN_SECONDS * 1000);
    autoreloadButton.setAttribute("enabled", true);
    autoreloadButton.style.opacity = 1;
  }
}

async function fetchAndApplySettings() {
  try {
    const res = await fetch('/api/settings');
    if (res.ok) {
      const settings = await res.json();

      UI_REFRESH_IN_SECONDS = settings.ui_refresher_s;
      //Enable autoreload
      document.getElementById("autoreload").style.display = "inline-block";
      document.getElementById("autoreload").title=`Autoreload every ${UI_REFRESH_IN_SECONDS} seconds`;

    } else {
      alert("Error loading settings: " + res.status);
      console.error("Error loading settings:", res.status);
    }
  } catch (err) {
    alert("Error loading settings: " + err)
    console.error("Error loading settings:", err);
  }
}

(function init() {
  fetchAndApplySettings();

  neonSwitches(
    document.querySelector('#sort-by-panel'), 
    (value) => {
      document.getElementById('sort-options').setAttribute('sort-by', value);
      fetchJobs();
     });

  neonSwitches(
    document.querySelector('#sort-order-panel'), 
    (value) => {
      document.getElementById('sort-options').setAttribute('sort-order', value);
      fetchJobs();
    });

  stickySwitches(
    document.querySelector('#filter-by-panel'), 
    (endState, value) => {
      const existingFilterBy = document.getElementById('filter-options').getAttribute('filter-by');
      if (endState == "on") {
        if (existingFilterBy.indexOf(value) == -1) {
          document.getElementById('filter-options').setAttribute('filter-by', existingFilterBy + " " + value);
        }
      } else {
        if (existingFilterBy.indexOf(value) != -1) {
          document.getElementById('filter-options').setAttribute('filter-by', existingFilterBy.replaceAll(value, "").trim());
        }
      }
      fetchJobs();
    });

  //Enough with those one off functions
  (() =>  {
    const orderingPanelSwitch = document.querySelector("#ordering-panel-switch");
    const filterPanelSwitch = document.querySelector("#filter-panel-switch");
    const orderingPanel = document.querySelector("#ordering-panel");
    const filterPanel = document.querySelector("#filter-panel");

    const showOrderingPanel = () => {
      orderingPanelSwitch.querySelector('i').classList.remove('bi-filter-circle');
      orderingPanelSwitch.querySelector('i').classList.add('bi-filter-circle-fill');
      orderingPanel.classList.remove("hidden");
    }

    const hideOrderingPanel = () => {
      orderingPanelSwitch.querySelector('i').classList.remove('bi-filter-circle-fill');
      orderingPanelSwitch.querySelector('i').classList.add('bi-filter-circle');
      orderingPanel.classList.add("hidden");
    }

    const showFilterPanel = () => {
      filterPanelSwitch.querySelector('i').classList.remove('bi-funnel');
      filterPanelSwitch.querySelector('i').classList.add('bi-funnel-fill');
      filterPanel.classList.remove("hidden");
    }

    const hideFilterPanel = () => {
      filterPanelSwitch.querySelector('i').classList.remove('bi-funnel-fill');
      filterPanelSwitch.querySelector('i').classList.add('bi-funnel');
      filterPanel.classList.add("hidden");
    }

    orderingPanelSwitch.onclick = () => {
      if(orderingPanel.classList.contains("hidden")) {
        hideFilterPanel();
        showOrderingPanel();
      } else {
        hideOrderingPanel();
      }
    }

    filterPanelSwitch.onclick = () => {
      if(filterPanel.classList.contains("hidden")){
        hideOrderingPanel();
        showFilterPanel()
      } else {
        hideFilterPanel()
      }
    }

  })();

  fetchJobs();
})();
