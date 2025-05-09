function getQueryParam(param) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(param);
}

async function loadJob(name) {
  const urlEncodedName = encodeURIComponent(name);
  
  fetch(`/api/jobs/${urlEncodedName}`)
  .then(response => {
    if (response.ok) {
      return response.json();
    } else if (response.status == 404) {
      document.getElementById("page-title").innerText = "Job not found";
      throw new Error("Job not found");
    } else {
      document.getElementById("page-title").innerText = "Failed to load job";
      throw new Error("Error loading job: " + response.status);
    }
  })
  .then(job => {
    //Change page title
    document.getElementById("page-title").innerText = "Edit";

    //Enable export button
    document.getElementById("job-export-btn").href = `/data/jobs/${urlEncodedName}`;
    document.getElementById("job-export-btn").style.display = "inline-block";

    //Change submit button label
    document.getElementById("job-submit-btn").innerText = "Update";

    // Configure and show the delete button
    document.getElementById("job-delete-btn").onclick = (e) => deleteJob(job.name);
    document.getElementById("job-delete-btn").style.display = "inline-block";

    populateFormFromJob(job);
  })
  .catch(error => {
    document.getElementById("page-title").innerText = "Failed to load job";
    throw new Error("Error loading job: " + error);
  });
}

document.getElementById("job-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const job = createJobFromForm(form);

  try {
    // Determine if we are editing an existing job or creating a new one.
    const isEdit = document.getElementById("job-name").disabled; // Name input is disabled if editing
    let method = isEdit ? "PUT" : "POST";
    let url = '/api/jobs';
    if (isEdit) {
      url += `/${encodeURIComponent(job.name)}`;
    }

    const headers = { "Content-Type": "application/json" };
    if (document.getElementById("skip-path-existence-check").checked) {
      headers["Skip-Path-Existence-Check"] = "True";
    }

    const res = await fetch(url, {
      method,
      headers: headers,
      body: JSON.stringify(job),
    });

    if (res.ok) {
      window.location.href = "index.html";
    } else if (res.status == 404) {
      alert("Job not found");
    } else if (res.status == 400) {
      const response = await res.json();
      updateViolations(response.validation);
    } else {
      alert("Error saving job: " + res.status);
      console.error("Error saving job:", res.status);
    }
  } catch (err) {
    alert("Error saving job: " + err);
    console.error("Error saving job: ", err);
  }
});

async function deleteJob(name) {
  if (!confirm(`Are you sure you want to delete the job "${name}"?`)) 
    return;
  try {
    const res = await fetch(`/api/jobs/${encodeURIComponent(name)}`, { method: "DELETE" });

    if (res.ok) {
      window.location.href = "index.html";
    } else if (res.status == 404) {
      alert("Job not found");
    } else {
      alert("Error deleting job: " + res.status);
      console.error("Error deleting job:", res.status);
    }
  } catch (err) {
    alert("Error deleting job: " + err);
    console.error("Error deleting job: ", err);
  }
}

function updateViolations(validation) {
  const newInvalidFormElements = [];

  // Mark invalid fields
  validation.forEach(violation => {
    const fieldName = Object.keys(violation)[0];
    const violationMsg = violation[fieldName];

    const formFieldId = `job-${fieldName}`;
    invalidElement = document.getElementById(formFieldId);
    newInvalidFormElements.push(formFieldId)

    invalidElement.setAttribute("class", "invalid");
    invalidElement.setAttribute("title", violationMsg);
  });

  // Unmark previous fields that got fixed
  INVALID_FORM_ELEMENTS.forEach(previouslyInvalidElementId => {
    if (!newInvalidFormElements.includes(previouslyInvalidElementId)) {
      previouslyInvalidElement = document.getElementById(previouslyInvalidElementId);
      previouslyInvalidElement.removeAttribute("class");
      previouslyInvalidElement.removeAttribute("title");
    }
  });

  // Store the current violations
  INVALID_FORM_ELEMENTS.length = 0;
  INVALID_FORM_ELEMENTS.push(...newInvalidFormElements);
}


function populateFormFromJob(job) {
  document.getElementById("job-name").value = job.name;
  document.getElementById("job-name").disabled = true; // Disable editing the job name when editing
  document.getElementById("job-description").value = job.description;
  document.getElementById("job-scope").value = job.scope;
  document.getElementById("job-scope").disabled = true; // Disable editing the job scope when editing
  document.getElementById("job-schedule").value = job.schedule;      
  document.getElementById("job-source").value = job.source;
  document.getElementById("job-dest").value = job.dest;
  document.getElementById("job-allowed_percentage").value = job.allowed_percentage;
  document.getElementById("job-reporter_o2").checked = job.reporter_o2;
  document.getElementById("job-reporter_discord").checked = job.reporter_discord;
  document.getElementById("job-report_noop").checked = job.report_noop;
}

function createJobFromForm(form) {
  return {
    name: form.name.value.trim(),
    description: form.description.value.trim(),
    scope: form.scope.value,
    schedule: form.schedule.value,
    source: form.source.value.trim(),
    dest: form.dest.value.trim(),
    allowed_percentage: parseInt(form.allowed_percentage.value),
    reporter_o2: form.reporter_o2.checked,
    reporter_discord: form.reporter_discord.checked,
    report_noop: form.report_noop.checked,
  };
}

// On page load, check if we are in edit mode by looking for a job name parameter
const jobNameParam = getQueryParam("name");
if (jobNameParam) {
  loadJob(jobNameParam);
} else {
  //Enable import button
  //document.getElementById("job-import-btn").href = `/data/jobs/${urlEncodedName}`;
  //document.getElementById("job-import-btn").style.display = "inline-block";
}

// Cache of the current invalid form elements.
// It's used for clearing up the status of invalid elements in an efficient way
const INVALID_FORM_ELEMENTS = []
