# Mirror Jobs Manager

A lightweight web-based management interface for scheduling mirror jobs via systemd timers and services. This project uses a Flask backend to handle job CRUD (Create, Read, Update, Delete) operations and stores each job in a YAML file. The client-side frontend is built with plain HTML, CSS, and JavaScript (no React) to keep things simple.

## Table of Contents

- [Overview](#overview)
- [Folder Structure](#folder-structure)
- [Installation and Setup](#installation-and-setup)
- [Usage](#usage)
- [Customization and Development](#customization-and-development)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)
- [License](#license)

## Overview

This project provides a simple dashboard to manage "mirror jobs" that you want to run on your system using systemd. The jobs are defined through the following properties:

- **Job Name & Description:** Identify and describe the job.
- **Scope:** Choose between a user-level or system-level job.
- **Paths:** Define the source and destination paths.
- **Allowed Percentage:** The allowed percentage difference that may be used in comparing the source and destination.
- **Enabled/Disabled:** Toggle job activation.

When a job is created, the backend calls a shell script (`install.sh`) to generate and enable a corresponding systemd timer and service. Similarly, disabling or deleting a job unregisters it via `uninstall.sh`.

## Folder Structure

```plaintext
your-project/
├── app.py                  # Flask backend API and static file server
├── install.sh              # Shell script to register a job with systemd
├── uninstall.sh            # Shell script to unregister a job from systemd
├── jobs/                   # Directory to store individual job YAML files
├── requirements.txt        # Python dependencies (Flask, PyYAML, Flask-CORS)
└── static/
    ├── index.html          # Static HTML frontend
    ├── main.js             # JavaScript for frontend functionality
    └── style.css           # Optional CSS styling
```

## Installation and Setup

1. Clone the Repository:
    ```
    git clone <repository-url>
    cd mirrorr
    ```
1. Install Python Dependencies (optionally in Virtual Environment):
    ```
    apt install python3-flask
    apt install python3-yaml
    apt install python3-flask-cors
    ```
1. Run the Flask Server:
    ```
    python app.py
    ```
1. Access the Frontend:
   
    Open your browser and navigate to http://\<your-ip>:5000
   
    (replace <your-ip> with the IP address of the machine running Flask).

## Usage

#### View Jobs:
The homepage (index.html) lists all mirror jobs with their status (enabled or disabled) by fetching data from the /api/jobs endpoint.

#### Create a New Job:
Use the “Create New Job” form to enter job details (name, description, scope, source, destination, allowed percentage, and activation). When submitted, the job is saved in YAML format in the jobs/ folder and the systemd job is registered via the install.sh script.

#### Toggle a Job’s Status:
Each job listing includes a button to enable or disable the job. This sends a request to update the job’s status and updates the systemd settings accordingly.

#### Delete a Job:
Use the “Delete” button to remove a job. The job configuration file is deleted from the jobs/ folder, and the job is unregistered from systemd via the uninstall.sh script.

## Customization and Development
- Backend API (app.py):
Modify or extend endpoints as needed to suit more advanced job scheduling or logging requirements.

- Frontend (Static Files):
Edit index.html for the structure, style.css for design, and main.js for interactivity and API communication.

- Systemd Integration:
Adjust install.sh and uninstall.sh for deeper control or additional systemd configurations.

- Additional Features:
Consider adding a “Run Now” button, job history logs, or an authentication layer to secure job management.

## Troubleshooting

## Future Improvements

- Job Logs and Status:
Incorporate job run logs, last execution times, and systemd timer statuses.

- Manual Trigger:
Add a “Run Now” button to allow manual execution of jobs.

- Enhanced UI/UX:
Improve styling and form validation for a better user experience.

- Dockerization:
Create Docker containers (or a Docker Compose configuration) for easy deployment.

- Security:
Consider adding basic authentication to protect the API and the frontend if exposed publicly.

## License
MIT License

