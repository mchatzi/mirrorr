async function fetchJobs() {
  try {
    const response = await fetch('/api/jobs');
    if (response.ok) {
      const jobs = await response.json();
      renderJobs(jobs);
    } else if (response.status == 401) {
      window.location.reload();
      return;
    } else {
      document.getElementById("jobs-container").innerHTML = "Failed to load jobs";
      alert("Error loading jobs, status code:" + response.status);
      console.error("Error loading jobs, status code:" + response.status);
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

  filterJobs(jobs, document.getElementById("filter-panel-switch").getAttribute("filter-by"));

  updateStatusCounters(jobs);
  
  sortJobs(jobs, 
    document.getElementById("ordering-panel-switch").getAttribute("sort-by"), 
    document.getElementById("ordering-panel-switch").getAttribute("sort-order"));

  jobs.forEach(job => {
    const urlEncodedJobName = encodeURIComponent(job.name);
    const next_run_str = job.next_run ? 
      CONFIGURATION["use_cool_timestamps"] ? printDurationFromNow(job.next_run, false) : 
      new Date(Math.abs(job.next_run * 1000)).toLocaleString(undefined, {dateStyle: "short", timeStyle: "short"})
      : null;

    const last_run_str = job.last_run ? 
      CONFIGURATION["use_cool_timestamps"] ? printDurationToNow(job.last_run, false) + ' ago' : 
      new Date(Math.abs(job.last_run * 1000)).toLocaleString(undefined, {dateStyle: "short", timeStyle: "short"})
      : null;

    const jobEl = document.createElement("div");
    jobEl.classList.add("job-item");
    if (job.enabled) {
      jobEl.classList.add("enabled");
    }

    jobEl.innerHTML = `
      <div class="job-info">
        <h3>${job.name}</h3>
        ${ job.description ?
          `<p class="job-description collapsible">${job.description}</p>` : '' }

        <p>
          <span class="blockable">
            <strong>Schedule:</strong><span class="fixed-width">${ CONFIGURATION["do_reverse_cron"] ? reverseCron(job.schedule) : job.schedule }</span>
          </span>
          
          ${ (job.rsync_delete && job.allowed_percentage) ? 
            `<span class="blockable collapsible"><strong>Allowed Percentage:</strong>${job.allowed_percentage}%</span>` : ''}
          
          <span class="blockable">
            ${(job.status == 'running' ? `<strong>Running for:</strong>${job.started_at ? printDurationToNow(job.started_at, false) : 'no info'}` :
              `<strong>Last run:</strong>${job.last_run ? (last_run_str[0] == '-' ? last_run_str.substring(1) : last_run_str ) : 'Never'}`)}
          </span>

          <span class="blockable">
            ${job.status != 'running' && next_run_str ? 
              (next_run_str[0] == '-' ?
                `<strong>Queued:</strong>${next_run_str.substring(1)}` :
                `<strong>Next run:</strong>${next_run_str}`) : '' }
          </span>
            
          <span class="collapsible">
            ${(job.rsync_no_owner || job.rsync_no_group || job.rsync_no_perms || job.rsync_acls || job.rsync_no_times ||
              job.rsync_in_place || job.rsync_whole_file || job.rsync_fsync || job.rsync_bwlimit || job.rsync_delete ||
              job.rsync_nice || job.rsync_ionice || job.reporter_o2 || job.reporter_discord || job.debug || job.rsync_verbose || job.rsync_cvs_exclude) ?
              "<br/>" : ""}

            ${job.rsync_no_owner ? '<strong class="rsync-active-option" title="Will not try to change ownership to folders and files on destination">no-owner</strong>' : ''}
            ${job.rsync_no_group ? '<strong class="rsync-active-option" title="Will not try to change groups to folders and files on destination">no-group</strong>' : ''}
            ${job.rsync_no_perms ? '<strong class="rsync-active-option" title="Will not try to change permissions to folders and files on destination">no-perms</strong>' : ''}
            ${job.rsync_acls ? '<strong class="rsync-active-option" title="Will apply acls to folders and files on destination">acls</strong>' : ''}
            ${job.rsync_no_times ? '<strong class="rsync-active-option" title="Will not try to set times on folders and files on destination">no-times</strong>' : ''}
            ${job.rsync_in_place ? '<strong class="rsync-active-option" title="Will not create temporary files on destination">in-place</strong>' : ''}
            ${job.rsync_whole_file ? '<strong class="rsync-active-option" title="Will not do delta transfers; it always send whole file">whole-file</strong>' : ''}
            ${job.rsync_fsync ? '<strong class="rsync-active-option" title="Will use fsync and try flushing data immediately to destination">fsync</strong>' : ''}
            ${job.rsync_cvs_exclude ? '<strong class="rsync-active-option" title="Will skip version control files">cvs-exclude</strong>' : ''}

            ${job.rsync_bwlimit ? '<strong class="rsync-active-option" title="Limit the trasnfer speed">bwlimit: ' +
              ({ 2000000: "2GB/s", 1000000: "1GB/s", 500000: "500MB/s", 250000: "250MB/s", 100000: "100MB/s", 80000: "80MB/s",
                60000: "60MB/s", 40000: "40MB/s", 30000: "30MB/s", 20000: "20MB/s", 10000: "10MB/s", 1000: "1MB/s", 100: "100KB/s" })
                [job.rsync_bwlimit] + '</strong>' : ''}

            ${job.rsync_delete ? '<strong class="rsync-active-option" title="Will perform deletions on destination">delete</strong>' : ''}
            ${job.rsync_nice ? '<strong class="rsync-active-option" title="Will use nice in front of rsync">Nice (' + job.rsync_nice + ')</strong>' : ''}
            ${job.rsync_ionice ? '<strong class="rsync-active-option" title="How much nice should it be">Ionice (' + job.rsync_ionice + ')</strong>' : ''}

            ${job.reporter_o2 ? '<strong class="rsync-active-option" title="Uses OpenObserve reporter">o2</strong>' : ''}
            ${job.reporter_discord ? '<strong class="rsync-active-option" title="Uses Discord reporter"><i class="bi bi-discord"></i></strong>' : ''}
            ${job.debug ? '<strong class="rsync-active-option debug" title="Is in debug mode"><i style="color:#4a4aeb" class="bi bi-bug"></i></strong>' : ''}
            ${job.rsync_verbose ? '<strong class="rsync-active-option verbose" title="Will log verboselly"><i style="color:#baab01" class="bi bi-journal-text"></i></strong>' : ''}
          </span>
        </p>
        <p class="from-to-label collapsible"><strong>From → To:</strong>&nbsp;&nbsp;<code>${job.source} → ${job.dest}</code></p>
      </div>
      <div class="job-sidebar">
        <label class="switch" title="${job.enabled ? 'Disable' : 'Enable'}">
          <input type="checkbox" ${job.enabled ? 'checked' : ''} onchange="toggleJobStatus('${job.name}', event)" />
          <span class="slider"></span>
        </label>
        <label class="dryrun-label" title="${job.dryruns ? 'Run normally' : 'Run in dry mode'}">
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

function updateStatusCounters(jobs) {
  const enabledCount = jobs.filter(job => job.enabled).length;
  const disabledCount = jobs.filter(job => job.enabled == false).length;
  document.getElementById("status-counters").innerHTML = 
    `<span>(<span 
      class="counter enabled" title="${enabledCount} enabled jobs">${enabledCount}</span>/<span 
      class="counter disabled" title="${disabledCount} disabled jobs">${disabledCount}</span>)</span>`;
}

function updateDebugModes(jobs) {
  const jobInDebugMode = jobs.filter(job => job.debug && job.enabled).length != 0;
  document.querySelector("#job-in-debug-mode").style.display = jobInDebugMode ? 'block' : 'none';

  const jobInVerboseMode = jobs.filter(job => job.rsync_verbose && job.enabled).length != 0;
  document.querySelector("#job-in-verbose-mode").style.display = jobInVerboseMode ? 'block' : 'none';
}

async function toggleJobStatus(name, element) {
  //checkbox hasn't changed yet state
  enable = !element.target.checked ? false : true;

  try {
    const response = await fetch(`/api/jobs/${encodeURIComponent(name)}/toggle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ "enable": enable })
    });

    if (response.ok) {
      const status = await response.json();
      if (status['error']) {
        alert("Error toggling job: " + status['error']);
        console.error("Error toggling job: " + status['error']);
      }
    } else if (response.status == 401) {
      window.location.reload();
      return;
    } else {
      alert("Error toggling job: " + response.status);
      console.error("Error toggling job: ", response.status);
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
    const response = await fetch(`/api/jobs/${encodeURIComponent(name)}/stop`, {
      method: "GET"
    });

    if (response.ok) {
      const status = await response.json();
      if (status['error']) {
        alert("Error stopping job: " + status['error']);
        console.error("Error stopping job: " + status['error']);
      } else {
        fetchJobs();
      }
    } else if (response.status == 401) {
      window.location.reload();
      return;
    } else {
      alert("Error stopping job: " + response.status);
      console.error("Error stopping job: ", response.status);
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
    const response = await fetch(`/api/jobs/${encodeURIComponent(name)}/dryruns`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ "enable": enable })
    });

    if (response.ok) {
      const status = await response.json();
      if (status['error']) {
        alert("Error toggling dry runs: " + status['error']);
        console.error("Error toggling dry runs: " + status['error']);
      }
    } else if (response.status == 401) {
      window.location.reload();
      return;
    } else {
      alert("Error toggling dry runs: " + response.status);
      console.error("Error toggling dry runs: ", response.status);
    }
    fetchJobs();
  } catch (err) {
    alert("Error toggling dry runs: " + err);
    console.error("Error toggling dry runs: ", err);
  }
}

function autoreload(autoreloadButton) {
  const enabled = autoreloadButton.hasAttribute("enabled");
  const interval = parseInt(autoreloadButton.getAttribute("interval"));

  if (enabled) {
    clearInterval(INTERVAL_ID);
    autoreloadButton.removeAttribute("enabled");
    autoreloadButton.querySelector("i").style.opacity = 0.4;
  } else {
    fetchJobs();
    INTERVAL_ID = setInterval(fetchJobs, interval * 1000);
    autoreloadButton.setAttribute("enabled", true);
    autoreloadButton.querySelector("i").style.opacity = 1;
  }
}


async function updateSettings(settings) {
  try {
    const response = await fetch('/api/settings', {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });

    if (response.ok) {
      ;
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
      const errMsg = "Validation error(s), your preference was not saved. Errors: \n" + errors.join("\n");
      alert(errMsg);
      console.error(errMsg);
    } else {
      const error = await response.text();
      alert("Something went wrong, your preference was not saved. Error: " + error)
      console.error(`Something went wrong, your preference was not saved. Error: ${response.status}, ${error}`)
    }
  } catch (err) {
    alert("Error saving settings: " + err)
    console.error("Error saving settings:", err);
  }
}

function initOrderingAndFilterPanels() {
  const sortBy = CONFIGURATION["job_ordering"].split('/')[0].trim();
  const sortOrder = CONFIGURATION["job_ordering"].split('/')[1].trim();
  const orderingPanel = document.querySelector('#ordering-panel');
  const orderingPanelSwitch = document.querySelector("#ordering-panel-switch");

  orderingPanelSwitch.setAttribute('sort-by', sortBy);
  orderingPanelSwitch.setAttribute('sort-order', sortOrder);
  orderingPanel.querySelector(`#sort-by-panel .neon-switch[value="${sortBy}"]`).classList.add("on");
  orderingPanel.querySelector(`#sort-order-panel .neon-switch[value="${sortOrder}"]`).classList.add("on");

  neonSwitches(
    document.querySelector('#sort-by-panel'), 
    (value) => {
      orderingPanelSwitch.setAttribute('sort-by', value);
      fetchJobs();
      updateSettings({
        "job_ordering": value + " / " + orderingPanelSwitch.getAttribute('sort-order')
      });
    });

  neonSwitches(
    document.querySelector('#sort-order-panel'), 
    (value) => {
      orderingPanelSwitch.setAttribute('sort-order', value);
      fetchJobs();
      updateSettings({
        "job_ordering": orderingPanelSwitch.getAttribute('sort-by') + " / " + value
      });
    });

  stickySwitches(
    document.querySelector('#filter-by-panel'), 
    (endState, value) => {
      const filterPanelSwitch = document.querySelector("#filter-panel-switch");
      const existingFilterBy = filterPanelSwitch.getAttribute('filter-by');

      if (endState == "on") {
        if (existingFilterBy.indexOf(value) == -1) {
          filterPanelSwitch.setAttribute('filter-by', existingFilterBy + " " + value);
        }
      } else {
        if (existingFilterBy.indexOf(value) != -1) {
          filterPanelSwitch.setAttribute('filter-by', existingFilterBy.replaceAll(value, "").trim());
        }
      }
      fetchJobs();
    });

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
}

function initJobviewLayoutSelector() {
  const jobViewLayout = CONFIGURATION["job_view_layout"];
  const toggleJobViewLayoutButtton = document.querySelector("a.toggle-view-button");

  toggleJobViewLayoutButtton.setAttribute("job-view-layout", jobViewLayout);

  const viewSetToListing = () => {
    toggleJobViewLayoutButtton.setAttribute("job-view-layout", "listing");
    toggleJobViewLayoutButtton.title = "View as grid";
    const i = toggleJobViewLayoutButtton.querySelector("i")
    i.classList.remove("bi-chevron-expand");
    i.classList.add("bi-chevron-contract");
  }

  const viewSetToGrid = () => {
    toggleJobViewLayoutButtton.setAttribute("job-view-layout", "grid");
    toggleJobViewLayoutButtton.title = "View as listing";
    const i = toggleJobViewLayoutButtton.querySelector("i")
    i.classList.remove("bi-chevron-contract");
    i.classList.add("bi-chevron-expand");
  }

  if (jobViewLayout == "listing") {
    viewSetToListing();
  } else {
    viewSetToGrid();
  }

  toggleJobViewLayoutButtton.onclick = () => {
    toggleJobviewLayout(toggleJobViewLayoutButtton.getAttribute("job-view-layout"), 
      viewSetToListing, viewSetToGrid);
  }
}

(function init() {
  initJobviewLayoutSelector();
  initOrderingAndFilterPanels();
  fetchJobs();
})();
