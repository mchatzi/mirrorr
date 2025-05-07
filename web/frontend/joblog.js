function getQueryParam(param) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(param);
}

async function loadJobLog(name, index) {
  try {
    const res = await fetch(`/api/jobs/${encodeURIComponent(name)}/logs` +
        (index ? `?index=${index}` : ''));

    if (! (res.ok || res.status == 404)) {
      document.getElementById("page-title").innerText = "Failed to load logs";
      alert("Error loading logs: " + res.status);
      console.error("Error loading logs:", res.status);
      return;
    } 

    const data = await res.json();

    if (res.ok) {
      document.getElementById("page-title").innerText = `Log for ${name}` + (index && index != '0' ? ` [${index}]` : '');
      document.getElementById("log-download-btn").href = `/data/logs/${name}${(index ? `.${index}` : '')}.log`;
      document.getElementById("log-download-btn").style.display = "inline-block";

      if (data['too_big']) {
        document.getElementById("full-log-content").outerHTML = `<p>Log is too big (${data['too_big']}). Get the file <a href="/data/logs/${name}.log">here</a></p>`;
      } else {
        document.getElementById("full-log-content").innerText = data.content;
      }
    } else if (res.status == 404) {
      document.getElementById("page-title").innerText = `No log for ${name}` + (index ? ` with index ${index}` : '') + ' found';
    }

    if (data['all-logs']) {
      document.getElementById("all-logs").innerHTML = data['all-logs']
          .map(logIndex => `<a href="joblog.html?name=${encodeURIComponent(name)}&index=${logIndex}">${logIndex}</a>`).join(", ");

      if (data['all-logs'].length > 0) {
        // Logs exist, so enable the purge button
        document.getElementById("logs-purge-btn").onclick = (e) => purgeJobLogs(name);
        document.getElementById("logs-purge-btn").style.display = "inline-block";
      }
    }
  } catch (err) {
    document.getElementById("page-title").innerText = "Failed to load logs";
    alert("Error loading logs: " + err);
    console.error("Error loading logs:", err);
  }
}

// On page load, check if we are in edit mode by looking for a job name parameter
const jobNameParam = getQueryParam("name");
const jobLogIndexParam = getQueryParam("index");
if (jobNameParam) {
  loadJobLog(jobNameParam, jobLogIndexParam);
}

async function purgeJobLogs(name) {
  if (!confirm(`Are you sure you want to purge all logs for job "${name}"?`)) 
    return;
  try {
    const res = await fetch('/api/jobs/${name}/logs', { method: "DELETE" });

    if (res.ok) {
      window.location.reload();
    } else if (res.status == 404) {
      alert("Job not found");
    } else {
      alert("Error deleting logs: " + res.status);
      console.error("Error deleting logs: ", res.status);
    }
  } catch (err) {
    alert("Error deleting logs: : " + err);
    console.error("Error deleting logs: ", err);
  }
}


