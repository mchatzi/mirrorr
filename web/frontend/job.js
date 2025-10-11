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
  document.getElementById("job-schedule").value = job.schedule;
  document.getElementById("job-source").value = job.source;
  document.getElementById("job-dest").value = job.dest;
  document.getElementById("job-allowed_percentage").value = job.allowed_percentage;
  document.getElementById("job-reporter_o2").checked = job.reporter_o2;
  document.getElementById("job-reporter_discord").checked = job.reporter_discord;
  document.getElementById("job-report_noop").checked = job.report_noop;
  document.getElementById("job-rsync_no_owner").checked = job.rsync_no_owner;
  document.getElementById("job-rsync_no_group").checked = job.rsync_no_group;
  document.getElementById("job-rsync_no_perms").checked = job.rsync_no_perms;
  document.getElementById("job-rsync_no_times").checked = job.rsync_no_times;
  document.getElementById("job-rsync_delete").checked = job.rsync_delete;
  document.getElementById("job-rsync_in_place").checked = job.rsync_in_place;
  document.getElementById("job-rsync_whole_file").checked = job.rsync_whole_file;
  document.getElementById("job-rsync_fsync").checked = job.rsync_fsync;
  document.getElementById("job-rsync_bwlimit").value = job.rsync_bwlimit || "";
  document.getElementById("job-rsync_nice").value = job.rsync_nice || "";
  document.getElementById("job-rsync_ionice").value = job.rsync_ionice || "";

}

function createJobFromForm(form) {
  return {
    name: form.name.value.trim(),
    description: form.description.value.trim(),
    schedule: form.schedule.value,
    source: form.source.value.trim(),
    dest: form.dest.value.trim(),
    allowed_percentage: parseInt(form.allowed_percentage.value),
    reporter_o2: form.reporter_o2.checked,
    reporter_discord: form.reporter_discord.checked,
    report_noop: form.report_noop.checked,
    rsync_no_owner: form.rsync_no_owner.checked,
    rsync_no_group: form.rsync_no_group.checked,
    rsync_no_perms: form.rsync_no_perms.checked,
    rsync_no_times: form.rsync_no_times.checked,
    rsync_delete: form.rsync_delete.checked,
    rsync_in_place: form.rsync_in_place.checked,
    rsync_whole_file: form.rsync_whole_file.checked,
    rsync_fsync: form.rsync_fsync.checked,
    rsync_bwlimit: form.rsync_bwlimit.value,
    rsync_nice: form.rsync_nice.value,
    rsync_ionice: form.rsync_ionice.value,
  };
}


document.getElementById("job-import-btn").addEventListener('click', (e) => {
  e.preventDefault();
  document.getElementById("job-import-file").click();
});

document.getElementById("job-import-file").addEventListener('change', async (e) => {
  const fileInput = e.target;
  const file = fileInput.files[0];
  if (!file) {
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  fetch('/data/jobs', {
    method: 'POST',
    body: formData
  }).then(async (response) => {
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`${response.status}, ${error}`);
    } else {
      window.location.href = "index.html";
    }
  }).catch(error => {
    console.error('Error importing job: ', error);
    alert('Error importing job: ' + error.message);
  });
});


// On page load, check if we are in edit mode by looking for a job name parameter
const jobNameParam = getQueryParam("name");
if (jobNameParam) {
  loadJob(jobNameParam);
} else {
  document.getElementById("job-import-btn").style.display = "inline-block";
}

// Cache of the current invalid form elements.
// It's used for clearing up the status of invalid elements in an efficient way
const INVALID_FORM_ELEMENTS = []
