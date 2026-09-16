/* Wizard JavaScript */

let currentStep = 1;
let dockerHostCount = 1;

function goToStep(n) {
    currentStep = n;
    document.querySelectorAll(".step").forEach(s => {
        const sn = parseInt(s.dataset.step);
        s.classList.remove("active", "done");
        if (sn < n) s.classList.add("done");
        if (sn === n) s.classList.add("active");
    });
    document.querySelectorAll(".step-panel").forEach(p => {
        p.classList.toggle("active", parseInt(p.dataset.step) === n);
    });
}

function toggleFields(name) {
    const checkbox = document.getElementById("use-" + name);
    const fields = document.getElementById(name + "-fields");
    fields.style.display = checkbox.checked ? "block" : "none";
}

function addDockerHost() {
    dockerHostCount++;
    const container = document.getElementById("docker-hosts");
    const entry = document.createElement("div");
    entry.className = "docker-host-entry";
    entry.innerHTML = `
        <div style="font-size:13px;font-weight:500;margin-bottom:8px;">Host ${dockerHostCount}</div>
        <div class="form-group">
            <label class="form-label">Friendly Name</label>
            <input class="form-input" type="text" placeholder="e.g. Media Server" />
        </div>
        <div class="form-row">
            <div class="form-group">
                <label class="form-label">Host / IP</label>
                <input class="form-input" type="text" placeholder="10.10.x.x" />
            </div>
            <div class="form-group" style="flex:0 0 80px;">
                <label class="form-label">Port</label>
                <input class="form-input" type="text" value="2376" />
            </div>
        </div>
        <div class="checkbox-group">
            <input type="checkbox" checked />
            <label>Use TLS</label>
        </div>
    `;
    container.appendChild(entry);
}

function generateSummary() {
    const container = document.getElementById("summary-content");
    let html = "";

    // Proxmox
    const endpoint = document.getElementById("proxmox-endpoint").value;
    const tokenId = document.getElementById("proxmox-token-id").value;
    if (endpoint && tokenId) {
        html += `<div class="summary-section">
            <div class="summary-title">Proxmox Cluster</div>
            <div class="summary-row"><strong>Endpoint:</strong> ${escapeHtml(endpoint)}</div>
            <div class="summary-row"><strong>Token:</strong> ${escapeHtml(tokenId)}</div>
        </div>`;
    }

    // Docker
    const hosts = collectDockerHosts();
    if (hosts.length > 0) {
        html += `<div class="summary-section"><div class="summary-title">Docker Hosts</div>`;
        hosts.forEach(h => {
            html += `<div class="summary-row"><strong>${escapeHtml(h.name || 'Host')}</strong>: ${escapeHtml(h.host)}:${h.port}</div>`;
        });
        html += `</div>`;
    }

    // Services
    const services = [];
    if (document.getElementById("use-grafana").checked) services.push("Grafana");
    if (document.getElementById("use-immich").checked) services.push("Immich");
    if (document.getElementById("use-nut").checked) services.push("NUT / UPS");

    if (services.length > 0) {
        html += `<div class="summary-section">
            <div class="summary-title">Services</div>
            <div class="summary-row"><strong>Enabled:</strong> ${services.join(", ")}</div>
        </div>`;
    }

    container.innerHTML = html || "<p class='empty-state'>No data sources configured. You'll be able to add them in the Admin panel later.</p>";
    goToStep(4);
}

function collectDockerHosts() {
    const entries = document.querySelectorAll("#docker-hosts .docker-host-entry");
    const hosts = [];
    entries.forEach(entry => {
        const inputs = entry.querySelectorAll("input");
        const name = inputs[0].value.trim();
        const host = inputs[1].value.trim();
        const port = inputs[2].value.trim() || "2376";
        const useTls = inputs[3].checked;
        if (host) {
            hosts.push({ name, host, port, use_tls: useTls });
        }
    });
    return hosts;
}

async function submitWizard() {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = "Saving...";

    try {
        const fd = new FormData();
        // Proxmox
        fd.append("proxmox_endpoint", document.getElementById("proxmox-endpoint").value);
        fd.append("proxmox_token_id", document.getElementById("proxmox-token-id").value);
        fd.append("proxmox_token_secret", document.getElementById("proxmox-token-secret").value);
        fd.append("track_vms", document.getElementById("track-vms").checked ? 1 : 0);
        fd.append("track_temps", document.getElementById("track-temps").checked ? 1 : 0);
        // Docker
        fd.append("docker_hosts_json", JSON.stringify(collectDockerHosts()));
        // Services
        fd.append("use_grafana", document.getElementById("use-grafana").checked ? 1 : 0);
        fd.append("grafana_url", document.getElementById("grafana-url").value);
        fd.append("grafana_api_key", document.getElementById("grafana-api-key").value);
        fd.append("use_immich", document.getElementById("use-immich").checked ? 1 : 0);
        fd.append("immich_url", document.getElementById("immich-url").value);
        fd.append("immich_api_key", document.getElementById("immich-api-key").value);
        fd.append("use_nut", document.getElementById("use-nut").checked ? 1 : 0);
        fd.append("nut_url", document.getElementById("nut-url").value);
        fd.append("nut_device", document.getElementById("nut-device").value);
        fd.append("nut_username", document.getElementById("nut-username").value);
        fd.append("nut_password", document.getElementById("nut-password").value);

        const res = await fetch("/api/wizard/submit", {
            method: "POST",
            body: fd
        });

        if (res.ok) {
            window.location.href = "/";
        } else {
            const err = await res.text();
            alert("Error saving configuration: " + err);
            btn.disabled = false;
            btn.textContent = "Save & Start Dashboard";
        }
    } catch (e) {
        alert("Error: " + e.message);
        btn.disabled = false;
        btn.textContent = "Save & Start Dashboard";
    }
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
}
