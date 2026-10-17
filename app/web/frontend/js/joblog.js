function getQueryParam(param) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(param);
}

async function loadJobLog(name, index) {
  const urlEncodedName = encodeURIComponent(name);
  try {
    const response = await fetch(`/api/jobs/${urlEncodedName}/logs` +
        (index ? `?index=${index}` : ''));

    if (! (response.ok || response.status == 404)) {
      document.getElementById("page-title").innerText = "Failed to load logs";
      alert("Error loading logs: " + response.status);
      console.error("Error loading logs:", response.status);
      return;
    } else if (response.status == 401) {
      window.location.reload();
      return;
    }

    const data = await response.json();

    if (response.ok) {
      document.getElementById("page-title").innerHTML = `Log for ${name}`;

      const numberOfLogs = data['all-logs'] ? data['all-logs'].length : 0;
      if (numberOfLogs > 1) {
        document.getElementById("section-log-nav").innerHTML = 
          getPreviousLogLink(urlEncodedName, index)  + 
          `<span class="current-log-index">${index || 0}</span>`  + 
          getNextLogLink(urlEncodedName, index, numberOfLogs);
      }     

      document.getElementById("log-download-btn").href = `/data/logs/${urlEncodedName}` + (index && index != '0' ? `.${index}` : '')+ '.log';
      document.getElementById("log-download-btn").style.display = "inline-block";

      if (data['too_big']) {
        document.getElementById("full-log-content").outerHTML = `<p>Log is too big (${data['too_big']}). Get the file <a href="/data/logs/${urlEncodedName}` + 
          (index && index != '0' ? `.${index}` : '') + '.log">here</a></p>';
      } else {
        document.getElementById("full-log-content").innerText = data.content;
      }
    } else if (response.status == 404) {
      document.getElementById("page-title").innerText = `No log for ${name}` + (index && index != '0' ? ` with index ${index}` : '') + ' found';
    }

    if (data['all-logs']) {
      const currentIndex = index || 0;
      document.getElementById("all-logs").innerHTML = data['all-logs']
          .map(logIndex => `<a 
            ${currentIndex == logIndex ? 'class="current"' : ''}
            href="joblog.html?name=${urlEncodedName}&index=${logIndex}">${logIndex}</a>`).join("&nbsp;&nbsp;");

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

function getPreviousLogLink(urlEncodedName, currentIndex) {
  if (currentIndex == null || currentIndex == 0) {
    return `<a class="log-nav disabled"><i class="bi bi-chevron-left"></i></a>`
  } else {
    return `<a class="log-nav" href="joblog.html?name=${urlEncodedName}&index=${currentIndex - 1}"><i class="bi bi-chevron-left"></i></a>`
  }
}

function getNextLogLink(urlEncodedName, currentIndex, numberOfLogs) {
  currentIndex = currentIndex == null ? 0 : parseInt(currentIndex);
  if (numberOfLogs <= 1 || currentIndex >= (numberOfLogs - 1)) {
    return `<a disabled class="log-nav disabled"><i class="bi bi-chevron-right"></i></a>`
  } else {
    return `<a class="log-nav" title="Next log" href="joblog.html?name=${urlEncodedName}&index=${currentIndex + 1}"><i class="bi bi-chevron-right"></i></a>`
  }
}

async function purgeJobLogs(name) {
  if (!confirm(`Are you sure you want to purge all logs for job "${name}"?`)) 
    return;
  try {
    const urlEncodedName = encodeURIComponent(name);
    const response = await fetch(`/api/jobs/${urlEncodedName}/logs`, { method: "DELETE" });

    if (response.ok) {
      window.location.href = `joblog.html?name=${urlEncodedName}`;
    } else if (response.status == 404) {
      alert("Job not found");
    } else if (response.status == 401) {
      window.location.reload();
      return;
    } else {
      alert("Error deleting logs: " + response.status);
      console.error("Error deleting logs: ", response.status);
    }
  } catch (err) {
    alert("Error deleting logs: : " + err);
    console.error("Error deleting logs: ", err);
  }
}


(function init() {
  const jobNameParam = getQueryParam("name");
  const jobLogIndexParam = getQueryParam("index");
  if (jobNameParam) {
    loadJobLog(jobNameParam, jobLogIndexParam);
  }
})();
