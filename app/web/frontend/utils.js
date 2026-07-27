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
