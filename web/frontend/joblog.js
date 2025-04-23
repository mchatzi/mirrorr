const API_BASE = "http://192.168.2.201:5000";

function getQueryParam(param) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(param);
}

async function loadJobLog(name, index) {
  try {
    const res = await fetch(`${API_BASE}/api/jobs/logs/${encodeURIComponent(name)}` +
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
      if (data['too_big']) {
        document.getElementById("full-log-content").outerHTML = `<p>Log is too big (${data['too_big']}). Get the file <a href="../data/logs/${name}.log">here</a></p>`;
      } else {
        document.getElementById("full-log-content").innerText = data.content;
      }
    } else if (res.status == 404) {
      document.getElementById("page-title").innerText = `No log for ${name} with index ${index} found`;
    }

    if (data['all-logs']) {
      document.getElementById("all-logs").innerHTML = data['all-logs']
          .map(logIndex => `<a href="joblog.html?name=${encodeURIComponent(name)}&index=${logIndex}">${logIndex}</a>`).join(", ");  
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

