/**
 * filebrowser js package for mirrorr
 */

function filebrowser(input) {
    const dropdown = document.getElementById(input.id + "-dropdown");
    let entries = [];
    let selectedIndex = -1;

    const abortController = new AbortController();

    const keyDownListener = (event) => {
        if (event.key === "ArrowDown") {
            event.preventDefault();
            selectNext();
        } else if (event.key === "ArrowUp") {
            event.preventDefault();
            selectPrevious();
        } else if (event.key === "Enter") {
            event.preventDefault();
            acceptSelection();
        } else if (event.key === "Escape") {
            closeDropdown();
        }
    };

    const inputListener = async () => {
        await fetchCompletions();
    };

    const blurListener = (event) => {
        closeDropdown();
    };

    input.addEventListener("input", inputListener);
    input.addEventListener("keydown", keyDownListener);
    input.addEventListener("blur", blurListener);    

    async function fetchCompletions() {
        const path = input.value;
        const rsyncRunsAsRoot = document.getElementById("job-run_rsync_as_root").checked;

        try {
            const response = await fetch(`/api/path-complete` +
                `?path=${encodeURIComponent(path)}` +
                `&rsyncRunsAsRoot=${rsyncRunsAsRoot}`,
                { signal: abortController.signal }
            );

            if (!response.ok) {
                closeDropdown();
                return;
            }

            const data = await response.json();
            entries = data.entries;
            selectedIndex = -1;

            if (data.status !== "ok") {
                renderError(data);
                return;
            }

            renderDropdown();
        } catch (error) {
            if (error.name !== "AbortError") {
                console.error("Path completion failed:", error);
            }
        }
    }

    function renderError(data) {
        dropdown.innerHTML = "";

        const item = document.createElement("div");
        item.className = "path-completion-error";

        if (data.status === "permission_denied") {
            item.textContent = "⚠ Permission denied";
        } else if (data.status === "not_found") {
            item.textContent = "⚠ Directory does not exist";
        } else if (data.status === "not_directory") {
            item.textContent = "⚠ Not a directory";
        } else {
            item.textContent = "⚠ Unknown error, see logs";
        }

        dropdown.appendChild(item);
        dropdown.hidden = false;
    }

    function renderDropdown() {
        dropdown.innerHTML = "";

        if (entries.length === 0) {
            closeDropdown();
            return;
        }

        for (let i = 0; i < entries.length; i++) {
            const entry = entries[i];
            const item = document.createElement("div");
            item.className = "path-completion-item";

            if (entry.directory === true) {
                item.classList.add("directory");
                item.textContent = entry.name + "/";
            } else if (entry.accessible === false) {
                item.classList.add("inaccessible");
                item.textContent = entry.name;
            } else {
                item.textContent = entry.name;
            }

            if (entry.accessible !== false) {
                item.addEventListener("mousedown", (event) => {
                    event.preventDefault();
                    selectedIndex = i;
                    acceptSelection();
                    
                });
            }
            dropdown.appendChild(item);
        }
        dropdown.hidden = false;
    }

    function selectNext() {
        if (entries.length === 0) {
            return;
        }

        selectedIndex++;
        if (selectedIndex >= entries.length) {
            selectedIndex = 0;
        }
        updateHighlight();
    }

    function selectPrevious() {
        if (entries.length === 0) {
            return;
        }

        selectedIndex--;
        if (selectedIndex < 0) {
            selectedIndex = entries.length - 1;
        }
        updateHighlight();
    }

    function updateHighlight() {
        const items = dropdown.children;
        for (let i = 0; i < items.length; i++) {
            items[i].classList.toggle(
                "selected",
                i === selectedIndex
            );
        }
    }

    function acceptSelection() {
        if (selectedIndex < 0 || selectedIndex >= entries.length) {
            return;
        }

        const entry = entries[selectedIndex];
        if (entry.accessible === false) {
            return;
        }

        input.value = entry.path;
        if (entry.directory === true) {
            input.value += "/";
            fetchCompletions();
            return;
        }
        closeDropdown();
    }

    function closeDropdown() {
        dropdown.hidden = true;
        selectedIndex = -1;
    }

    return function destroy() {
        abortController.abort();
        input.removeEventListener("input", inputListener);
        input.removeEventListener("keydown", keyDownListener);
        input.removeEventListener("blur", blurListener);
        closeDropdown();
    };
}