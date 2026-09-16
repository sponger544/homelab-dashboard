/* Admin Panel JavaScript */

document.addEventListener("DOMContentLoaded", () => {
    loadDataSources();
    loadStorageMounts();
    loadLinks();
    loadGroups();
    loadDockerUrls();
});

function showPanel(id) {
    document.querySelectorAll(".admin-panel").forEach(p => p.classList.remove("active"));
    document.querySelectorAll(".admin-nav-item").forEach(n => n.classList.remove("active"));
    document.getElementById("panel-" + id).classList.add("active");
    event.target.classList.add("active");
}

function closeModal(id) {
    document.getElementById(id).classList.remove("active");
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
}

/* ================= DATA SOURCES ================= */

async function loadDataSources() {
    try {
        const res = await fetch("/api/admin/data-sources");
        if (!res.ok) return;
        const sources = await res.json();
        const tbody = document.getElementById("data-sources-body");

        if (!sources.length) {
            tbody.innerHTML = "<tr><td colspan='5' class='empty-state'>No data sources configured.</td></tr>";
            return;
        }

        let html = "";
        sources.forEach(s => {
            const statusClass = s.is_active ? "" : "error";
            html += `<tr>
                <td>${escapeHtml(s.type)}</td>
                <td>${escapeHtml(s.name)}</td>
                <td style="font-size:11px;color:var(--muted);">${escapeHtml(s.endpoint)}</td>
                <td><span class="status-badge ${statusClass}">${s.is_active ? "active" : "disabled"}</span></td>
                <td>
                    <button class="btn btn-ghost" style="padding:4px 8px;font-size:11px;" onclick="toggleDataSource(${s.id})">Toggle</button>
                    <button class="btn btn-ghost" style="padding:4px 8px;font-size:11px;" onclick="deleteDataSource(${s.id})">Delete</button>
                </td>
            </tr>`;
        });
        tbody.innerHTML = html;
    } catch (e) {
        console.error(e);
    }
}

async function toggleDataSource(id) {
    try {
        await fetch(`/api/admin/data-sources/${id}/toggle`, { method: "POST" });
        loadDataSources();
    } catch (e) {
        alert("Error toggling data source");
    }
}

async function deleteDataSource(id) {
    if (!confirm("Delete this data source?")) return;
    try {
        await fetch(`/api/admin/data-sources/${id}`, { method: "DELETE" });
        loadDataSources();
    } catch (e) {
        alert("Error deleting data source");
    }
}

function showDataSourceModal() {
    document.getElementById("form-data-source").reset();
    document.getElementById("ds-id").value = "";
    document.getElementById("modal-ds-title").textContent = "Add Data Source";
    updateDsFields();
    document.getElementById("modal-data-source").classList.add("active");
}

function updateDsFields() {
    const type = document.getElementById("ds-type").value;
    const endpoint = document.getElementById("ds-endpoint");
    const extra = document.getElementById("ds-extra-fields");

    extra.innerHTML = "";

    if (type === "proxmox") {
        endpoint.placeholder = "https://10.10.x.x:8006";
        extra.innerHTML = `
            <div class="form-group"><label class="form-label">API Token ID</label><input class="form-input" type="text" id="ds-token-id" placeholder="root@pam!tokenname" /></div>
            <div class="form-group"><label class="form-label">API Token Secret</label><input class="form-input" type="password" id="ds-token-secret" placeholder="..." /></div>`;
    } else if (type === "docker") {
        endpoint.placeholder = "tcp://10.10.x.x:2376";
        extra.innerHTML = `
            <div class="form-row">
                <div class="form-group"><label class="form-label">Host IP</label><input class="form-input" type="text" id="ds-docker-host" placeholder="10.10.x.x" /></div>
                <div class="form-group" style="flex:0 0 80px;"><label class="form-label">Port</label><input class="form-input" type="text" id="ds-docker-port" value="2376" /></div>
            </div>
            <div class="checkbox-group"><input type="checkbox" id="ds-docker-tls" checked /><label>Use TLS</label></div>`;
    } else if (type === "grafana") {
        endpoint.placeholder = "http://10.10.x.x:3000";
    } else if (type === "immich") {
        endpoint.placeholder = "http://10.10.x.x:2283";
    } else if (type === "nut") {
        endpoint.placeholder = "http://10.10.x.x:3493";
        extra.innerHTML = `
            <div class="form-row">
                <div class="form-group"><label class="form-label">Device</label><input class="form-input" type="text" id="ds-nut-device" value="ups" /></div>
                <div class="form-group"><label class="form-label">Username</label><input class="form-input" type="text" id="ds-nut-user" value="monuser" /></div>
            </div>`;
    }
}

document.getElementById("form-data-source").addEventListener("submit", async (e) => {
    e.preventDefault();
    const type = document.getElementById("ds-type").value;
    const name = document.getElementById("ds-name").value;
    const endpoint = document.getElementById("ds-endpoint").value;

    let config = {};
    let secrets = {};

    if (type === "proxmox") {
        config = {};
        secrets = {
            token_id: document.getElementById("ds-token-id").value,
            token_secret: document.getElementById("ds-token-secret").value || document.getElementById("ds-secret").value
        };
    } else if (type === "docker") {
        const host = document.getElementById("ds-docker-host").value;
        const port = document.getElementById("ds-docker-port").value || "2376";
        const useTls = document.getElementById("ds-docker-tls").checked;
        config = { name, host, port: parseInt(port), use_tls: useTls };
    } else if (type === "grafana") {
        secrets = { api_key: document.getElementById("ds-api-key").value || document.getElementById("ds-secret").value };
    } else if (type === "immich") {
        secrets = { api_key: document.getElementById("ds-api-key").value || document.getElementById("ds-secret").value };
    } else if (type === "nut") {
        config = {
            device: document.getElementById("ds-nut-device").value,
        };
        secrets = {
            username: document.getElementById("ds-nut-user").value,
            password: document.getElementById("ds-secret").value
        };
    }

    const fd = new FormData();
    fd.append("type", type);
    fd.append("name", name);
    fd.append("endpoint", endpoint);
    fd.append("config_json", JSON.stringify(config));
    fd.append("secret_json", JSON.stringify(secrets));

    try {
        await fetch("/api/admin/data-sources", { method: "POST", body: fd });
        closeModal("modal-data-source");
        loadDataSources();
    } catch (err) {
        alert("Error saving: " + err.message);
    }
});

/* ================= STORAGE ================= */

async function loadStorageMounts() {
    try {
        const res = await fetch("/api/admin/storage-mounts");
        if (!res.ok) return;
        const mounts = await res.json();
        const tbody = document.getElementById("storage-body");

        if (!mounts.length) {
            tbody.innerHTML = "<tr><td colspan='5' class='empty-state'>No storage mounts configured.</td></tr>";
            return;
        }

        let html = "";
        mounts.forEach(m => {
            const statusClass = m.is_active ? "" : "error";
            html += `<tr>
                <td>${escapeHtml(m.host_label)}</td>
                <td>${escapeHtml(m.mount_path)}</td>
                <td>${escapeHtml(m.filesystem_type)}</td>
                <td><span class="status-badge ${statusClass}">${m.is_active ? "active" : "disabled"}</span></td>
                <td>
                    <button class="btn btn-ghost" style="padding:4px 8px;font-size:11px;" onclick="deleteStorageMount(${m.id})">Delete</button>
                </td>
            </tr>`;
        });
        tbody.innerHTML = html;
    } catch (e) {
        console.error(e);
    }
}

function showStorageModal() {
    document.getElementById("form-storage").reset();
    document.getElementById("modal-storage").classList.add("active");
}

document.getElementById("form-storage").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData();
    fd.append("host_label", document.getElementById("storage-host").value);
    fd.append("mount_path", document.getElementById("storage-mount").value);
    fd.append("filesystem_type", document.getElementById("storage-fstype").value);

    try {
        await fetch("/api/admin/storage-mounts", { method: "POST", body: fd });
        closeModal("modal-storage");
        loadStorageMounts();
    } catch (err) {
        alert("Error saving: " + err.message);
    }
});

async function deleteStorageMount(id) {
    if (!confirm("Delete this storage mount?")) return;
    try {
        await fetch(`/api/admin/storage-mounts/${id}`, { method: "DELETE" });
        loadStorageMounts();
    } catch (e) {
        alert("Error deleting");
    }
}

/* ================= LINKS & GROUPS ================= */

let groups = [];

async function loadGroups() {
    try {
        const res = await fetch("/api/admin/link-groups");
        if (!res.ok) return;
        groups = await res.json();
        updateGroupSelect();
    } catch (e) {
        console.error(e);
    }
}

function updateGroupSelect() {
    const sel = document.getElementById("link-group");
    sel.innerHTML = groups.map(g => `<option value="${g.id}">${escapeHtml(g.name)} (${g.tab})</option>`).join("");
}

async function loadLinks() {
    try {
        const res = await fetch("/api/admin/links");
        if (!res.ok) return;
        const links = await res.json();
        const tbody = document.getElementById("links-body");

        if (!links.length) {
            tbody.innerHTML = "<tr><td colspan='6' class='empty-state'>No links configured.</td></tr>";
            return;
        }

        let html = "";
        links.forEach(l => {
            const statusClass = l.is_visible ? "" : "error";
            html += `<tr>
                <td>${escapeHtml(l.name)}</td>
                <td>${escapeHtml(l.group_name)}</td>
                <td>${escapeHtml(l.group_id ? (groups.find(g=>g.id===l.group_id)||{}).tab || "") : ""}</td>
                <td style="font-size:11px;color:var(--muted);max-width:200px;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(l.url)}</td>
                <td><span class="status-badge ${statusClass}">${l.is_visible ? "visible" : "hidden"}</span></td>
                <td>
                    <button class="btn btn-ghost" style="padding:4px 8px;font-size:11px;" onclick="toggleLinkVisibility(${l.id})">Toggle</button>
                    <button class="btn btn-ghost" style="padding:4px 8px;font-size:11px;" onclick="deleteLink(${l.id})">Delete</button>
                </td>
            </tr>`;
        });
        tbody.innerHTML = html;
    } catch (e) {
        console.error(e);
    }
}

function showLinkModal() {
    document.getElementById("form-link").reset();
    document.getElementById("link-id").value = "";
    document.getElementById("modal-link-title").textContent = "Add Link";
    loadGroups();
    document.getElementById("modal-link").classList.add("active");
}

document.getElementById("form-link").addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("link-name").value;
    const url = document.getElementById("link-url").value;
    const groupId = parseInt(document.getElementById("link-group").value);
    const emojiIcon = document.getElementById("link-icon-emoji").value || "🔗";
    const urlIcon = document.getElementById("link-icon-url").value;

    let iconType = "emoji";
    let iconValue = emojiIcon;

    if (urlIcon) {
        iconType = "url";
        iconValue = urlIcon;
    }

    const fd = new FormData();
    fd.append("group_id", groupId);
    fd.append("name", name);
    fd.append("url", url);
    fd.append("icon_type", iconType);
    fd.append("icon_value", iconValue);

    try {
        await fetch("/api/admin/links", { method: "POST", body: fd });
        closeModal("modal-link");
        loadLinks();
    } catch (err) {
        alert("Error saving: " + err.message);
    }
});

async function toggleLinkVisibility(id) {
    // Fetch current link, flip visibility, update
    try {
        const res = await fetch("/api/admin/links");
        if (!res.ok) return;
        const links = await res.json();
        const link = links.find(l => l.id === id);
        if (!link) return;

        const fd = new FormData();
        fd.append("group_id", link.group_id);
        fd.append("name", link.name);
        fd.append("url", link.url);
        fd.append("icon_type", link.icon_type);
        fd.append("icon_value", link.icon_value);
        fd.append("is_visible", link.is_visible ? 0 : 1);

        await fetch(`/api/admin/links/${id}`, { method: "PUT", body: fd });
        loadLinks();
    } catch (e) {
        alert("Error toggling");
    }
}

async function deleteLink(id) {
    if (!confirm("Delete this link?")) return;
    try {
        await fetch(`/api/admin/links/${id}`, { method: "DELETE" });
        loadLinks();
    } catch (e) {
        alert("Error deleting");
    }
}

function showGroupModal() {
    document.getElementById("form-group").reset();
    document.getElementById("modal-group").classList.add("active");
}

document.getElementById("form-group").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData();
    fd.append("name", document.getElementById("group-name").value);
    fd.append("tab", document.getElementById("group-tab").value);

    try {
        await fetch("/api/admin/link-groups", { method: "POST", body: fd });
        closeModal("modal-group");
        loadGroups();
        loadLinks();
    } catch (err) {
        alert("Error saving: " + err.message);
    }
});

/* ================= DOCKER URLs ================= */

async function loadDockerUrls() {
    try {
        const res = await fetch("/api/admin/docker-url-overrides");
        if (!res.ok) return;
        const urls = await res.json();
        const tbody = document.getElementById("docker-urls-body");

        if (!urls.length) {
            tbody.innerHTML = "<tr><td colspan='5' class='empty-state'>No custom Docker container URLs configured.</td></tr>";
            return;
        }

        let html = "";
        urls.forEach(u => {
            html += `<tr>
                <td>${escapeHtml(u.host_name)}</td>
                <td style="font-size:11px;">${escapeHtml(u.container_id)}</td>
                <td style="font-size:11px;color:var(--muted);">${escapeHtml(u.custom_url)}</td>
                <td>${escapeHtml(u.display_name || "")}</td>
                <td>
                    <button class="btn btn-ghost" style="padding:4px 8px;font-size:11px;" onclick="deleteDockerUrl(${u.id})">Delete</button>
                </td>
            </tr>`;
        });
        tbody.innerHTML = html;
    } catch (e) {
        console.error(e);
    }
}

async function loadDockerHosts() {
    try {
        const res = await fetch("/api/admin/data-sources");
        if (!res.ok) return [];
        const sources = await res.json();
        return sources.filter(s => s.type === "docker");
    } catch (e) {
        return [];
    }
}

async function showDockerUrlModal() {
    const hosts = await loadDockerHosts();
    const sel = document.getElementById("du-host");
    sel.innerHTML = hosts.map(h => `<option value="${h.id}">${escapeHtml(h.name)}</option>`).join("");
    document.getElementById("form-docker-url").reset();
    document.getElementById("modal-docker-url").classList.add("active");
}

document.getElementById("form-docker-url").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData();
    fd.append("data_source_id", document.getElementById("du-host").value);
    fd.append("container_id", document.getElementById("du-container-id").value);
    fd.append("custom_url", document.getElementById("du-url").value);
    fd.append("display_name", document.getElementById("du-name").value);

    try {
        await fetch("/api/admin/docker-url-overrides", { method: "POST", body: fd });
        closeModal("modal-docker-url");
        loadDockerUrls();
    } catch (err) {
        alert("Error saving: " + err.message);
    }
});

async function deleteDockerUrl(id) {
    if (!confirm("Delete this URL override?")) return;
    try {
        await fetch(`/api/admin/docker-url-overrides/${id}`, { method: "DELETE" });
        loadDockerUrls();
    } catch (e) {
        alert("Error deleting");
    }
}
