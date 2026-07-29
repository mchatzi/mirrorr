/**
 * Utils js package for mirrorr
 */

function printDurationToNow(epoch, full = true) {
    if (!epoch || epoch === "") {
        return "";
    }
    return printDurationFromTo(epoch, Date.now() / 1000, full);
}

function printDurationFromNow(epoch, full = true) {
    if (!epoch || epoch === "") {
        return "";
    }
    return printDurationFromTo(Date.now() / 1000, epoch, full);
}

function printDurationFromTo(from, to, full = true) {
    if (!from || !to) {
        return "";
    }

    if (from > to) {
        return "-" + printDurationFromTo(to, from, full);
    }

    const duration_in_seconds = Math.floor(to - from);

    let minutes = Math.floor(duration_in_seconds / 60);
    let seconds = duration_in_seconds % 60;

    let hours = Math.floor(minutes / 60);
    minutes = minutes % 60;

    let days = Math.floor(hours / 24);
    hours = hours % 24;

    let months = Math.floor(days / 30);
    days = days % 30;

    let years = Math.floor(months / 12);
    months = months % 12;

    const parts = [
        [years, "y"],
        [months, "M"],
        [days, "d"],
        [hours, "h"],
        [minutes, "m"],
        [seconds, "s"],
    ];

    // Strip leading 0 entries
    const firstIdx = parts.findIndex(([value]) => value > 0);

    if (firstIdx === -1) {
        return "0s";
    }

    // Full mode: show everything after first non-zero.
    // Non-full mode: show only the two most significant parts.
    const displayParts = full
        ? parts.slice(firstIdx)
        : parts.slice(firstIdx, firstIdx + 2);

    return displayParts
        .map(([value, label]) => `${value}${label}`)
        .join("");
}

function neonSwitches(container, callback) {
    container.querySelectorAll(".neon-switch").forEach(neonSwitch => {
        neonSwitch.onclick = function(element) {
            //Turn off all switches
            container.querySelectorAll(".neon-switch.on").forEach(onSwitch => {
                onSwitch.classList.remove('on');
            });

            this.classList.add('on');
            callback(this.getAttribute('value'));
        }
    });
}


function stickySwitches(container, callback) {
    container.querySelectorAll(".neon-switch").forEach(neonSwitch => {
        neonSwitch.onclick = function(element) {
            endState = this.classList.contains("on") ? "off" : "on";
            this.classList.toggle('on');
            callback(endState, this.getAttribute('value'));
        }
    });
}

function sortJobs(jobs, sortBy, sortOrder) {
    if (!jobs || jobs.length === 0) {
        return;
    }

    if (sortBy == "name") {
        jobs.sort((job1, job2) => sortOrder == "asc" ?
            job1.name.localeCompare(job2.name) :
            job2.name.localeCompare(job1.name));

    } else if (sortBy == "last-run") {
        const jobsWithNoLastRun = jobs.filter(job => !job.last_run)
            .sort((job1, job2) => sortOrder == "asc" ?
            job1.name.localeCompare(job2.name) :
            job2.name.localeCompare(job1.name));

        jobs.splice(0, jobs.length, ...jobs.filter(job => job.last_run));
        jobs.sort((job1, job2) => sortOrder == "asc" ? 
            job1.last_run - job2.last_run :
            job2.last_run - job1.last_run);

        jobs.push(...jobsWithNoLastRun);

    } else if (sortBy == "next-run") {
        const jobHasNoNextRun = (job) => {
            return !job.next_run || job.status == 'running' || !job.enabled
        }

        const jobsWithNoNextRun = jobs.filter(jobHasNoNextRun)
            .sort((job1, job2) => sortOrder == "asc" ?
            job1.name.localeCompare(job2.name) :
            job2.name.localeCompare(job1.name));

        jobs.splice(0, jobs.length, ...jobs.filter(job => !jobHasNoNextRun(job)));
        jobs.sort((job1, job2) => sortOrder == "asc" ? 
            job2.next_run - job1.next_run :
            job1.next_run - job2.next_run);

        jobs.push(...jobsWithNoNextRun);

    }
}

function filterJobs(jobs, filterBy) {
    if (!jobs || jobs.length === 0) {
        return;
    }

    if (filterBy.indexOf("deletes") != -1) {
        jobs.splice(0, jobs.length, ...jobs.filter(job => job.rsync_delete));
    }
    if (filterBy.indexOf("disabled") != -1) {
        jobs.splice(0, jobs.length, ...jobs.filter(job => job.enabled == false));
    }
    if (filterBy.indexOf("no-reporter") != -1) {
        jobs.splice(0, jobs.length, ...jobs.filter(job => 
            job.reporter_discord != true && job.reporter_o2 != true));
    }
    if (filterBy.indexOf("uses-remotes") != -1) {
        jobs.splice(0, jobs.length, ...jobs.filter(job => 
            job.remote_dest == true || job.remote_source == true));
    }
    if (filterBy.indexOf("debugging") != -1) {
        jobs.splice(0, jobs.length, ...jobs.filter(job => job.debug == true));
    }
}
