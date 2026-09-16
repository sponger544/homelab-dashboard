/* Dashboard JavaScript */

document.addEventListener("DOMContentLoaded", () => {
    // Tab switching
    document.querySelectorAll(".tab").forEach(tab => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById(tab.dataset.tab).classList.add("active");
        });
    });

    // Collapsible sections
    document.querySelectorAll(".collapsible-header").forEach(header => {
        header.addEventListener("click", () => {
            header.parentElement.classList.toggle("open");
        });
    });

    // Load data
    loadStats();
    loadProxmoxVMs();
    loadLinks("internal");
    loadLinks("external");

    // Refresh every 30 seconds
    setInterval(loadStats, 30000);
    setInterval(loadProxmoxVMs, 60000);
});

async function loadStats() {
    try {
        const res = await fetch("/api/stats/stats");
        if (!res.ok) return;
        const data = await res.json();
        renderInfrastructure(data);
    } catch (e) {
        console.error("Error loading stats:", e);
    }
}

function renderInfrastructure(data) {
    const container = document.getElementById("infrastructure-stats");
    let html = "";

    // Proxmox card
    if (data.proxmox && data.proxmox.status === "ok") {
        const p = data.proxmox;
        const tempClass = p.avg_temp > 70 ? "hot" : "";
        html += `
            <div class="stat-card">
                <div class="stat-card-header">
                    <div class="stat-card-header-left">
                        <span class="dot green"></span>
                        <span class="stat-card-title">Proxmox Cluster</span>
                    </div>
                    <span class="temp-badge ${tempClass}">${Math.round(p.avg_temp)}°C</span>
                </div>
                <div class="stat-value">${p.total_vms} VMs</div>
                <div class="stat-sub">${p.online_nodes} nodes online</div>
                <div class="bar"><div class="bar-fill" style="width:${p.cpu_pct}%"></div></div>
                <div class="stat-sub" style="margin-top:4px;">CPU ${p.cpu_pct}% · RAM ${p.ram_pct}% (${p.ram_used_gb}/${p.ram_max_gb} GB)</div>
                <div class="net-stats">
                    <div>IN: <span>${p.net_in_mbps} Mbps</span></div>
                    <div>OUT: <span>${p.net_out_mbps} Mbps</span></div>
                </div>
            </div>
        `;
    }

    // Docker host cards
    data.docker_hosts.forEach(host => {
        const dotClass = host.running === host.total && host.running > 0 ? "green" : "amber";
        html += `
            <div class="stat-card clickable" onclick="openDockerModal(${host.id})">
                <div class="stat-card-header">
                    <div class="stat-card-header-left">
                        <span class="dot ${dotClass}"></span>
                        <span class="stat-card-title">Docker – ${escapeHtml(host.name)}</span>
                    </div>
                    <span class="view-all">View all ▸</span>
                </div>
                <div class="stat-value">${host.running}/${host.total}</div>
                <div class="stat-sub">containers running</div>
            </div>
        `;
    });

    // Immich card
    if (data.immich && data.immich.status === "ok") {
        const m = data.immich;
        html += `
            <div class="stat-card">
                <div class="stat-card-header">
                    <div class="stat-card-header-left">
                        <span class="dot green"></span>
                        <span class="stat-card-title">Immich</span>
                    </div>
                </div>
                <div class="stat-value">${m.total.toLocaleString()}</div>
                <div class="stat-sub">${m.usage_gb} GB used</div>
                <div class="stat-sub">${m.photos} photos · ${m.videos} videos</div>
            </div>
        `;
    }

    // NUT card
    if (data.nut && data.nut.status === "ok") {
        const n = data.nut;
        const onBattery = n.ups_status && n.ups_status.includes("OB");
        const dotClass = onBattery ? "amber" : "green";
        const powerText = n.real_power_w ? `${n.real_power_w}W` : "—";
        const runtimeText = n.runtime_minutes ? `~${n.runtime_minutes}m` : "—";
        const statusText = n.ups_status || "Online";
        html += `
            <div class="stat-card">
                <div class="stat-card-header">
                    <div class="stat-card-header-left">
                        <span class="dot ${dotClass}"></span>
                        <span class="stat-card-title">UPS (NUT)</span>
                    </div>
                </div>
                <div class="stat-value">${n.battery_charge || "—"}%</div>
                <div class="stat-sub">${statusText}</div>
                <div class="bar"><div class="bar-fill ${onBattery ? "amber" : "green"}" style="width:${n.battery_charge || 100}%"></div></div>
                <div class="stat-sub" style="margin-top:4px;">Power: <strong>${powerText}</strong> · Runtime: ${runtimeText}</div>
            </div>
        `;
    }

    container.innerHTML = html || '<p class="empty-state">No data sources configured yet. Add them in the Admin panel.</p>';
}

async function loadProxmoxVMs() {
    try {
        const res = await fetch("/api/stats/proxmox/vms");
        if (!res.ok) return;
        const vms = await res.json();
        const tbody = document.getElementById("proxmox-vms-body");

        if (!vms.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No Proxmox cluster configured.</td></tr>';
            return;
        }

        let html = "";
        vms.forEach(vm => {
            const statusClass = vm.status === "running" ? "" : (vm.status === "stopped" ? "error" : "warning");
            html += `
                <tr>
                    <td>${escapeHtml(vm.name)}</td>
                    <td>${vm.type}</td>
                    <td>${escapeHtml(vm.node)}</td>
                    <td><span class="status-badge ${statusClass}">${vm.status}</span></td>
                    <td>${vm.cpu}%</td>
                    <td>${vm.mem_used_gb}/${vm.mem_max_gb} GB</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (e) {
        console.error("Error loading VMs:", e);
    }
}

async function loadLinks(tab) {
    try {
        const res = await fetch(`/api/stats/links/${tab}`);
        if (!res.ok) return;
        const groups = await res.json();
        const container = document.getElementById(`${tab}-links`);

        if (!groups.length) {
            container.innerHTML = '<p class="empty-state">No links yet. Add some in the Admin panel.</p>';
            return;
        }

        let html = "";
        groups.forEach(group => {
            html += `<div class="links-section">
                <div class="links-section-title">${escapeHtml(group.group)}</div>
                <div class="links-grid">`;
            group.links.forEach(link => {
                const iconHtml = getIconHtml(link.icon_type, link.icon_value);
                html += `<a class="link-card" href="${escapeHtml(link.url)}" target="_blank" rel="noopener">
                    <div class="link-icon">${iconHtml}</div>
                    ${escapeHtml(link.name)}
                </a>`;
            });
            html += `</div></div>`;
        });
        container.innerHTML = html;
    } catch (e) {
        console.error("Error loading links:", e);
    }
}

function getIconHtml(type, value) {
    if (type === "url" || type === "upload") {
        const src = type === "upload" ? `/uploads/icons/${value}` : value;
        return `<img src="${src}" alt="" onerror="this.parentElement.textContent='🔗'" />`;
    }
    return value || "🔗";
}

async function openDockerModal(hostId) {
    const overlay = document.getElementById("docker-modal");
    const title = document.getElementById("docker-modal-title");
    const body = document.getElementById("docker-modal-body");

    overlay.classList.add("active");
    body.innerHTML = '<div class="spinner"></div> Loading...';

    try {
        const res = await fetch(`/api/stats/docker/${hostId}/containers`);
        if (!res.ok) {
            body.innerHTML = '<p class="empty-state">Failed to load containers.</p>';
            return;
        }
        const data = await res.json();
        title.textContent = `Docker – ${escapeHtml(data.host_name)}`;

        if (!data.containers.length) {
            body.innerHTML = '<p class="empty-state">No containers found.</p>';
            return;
        }

        let html = "";
        data.containers.forEach(c => {
            const dotClass = c.status === "running" ? "green" : "red";
            let actions = "";
            if (c.ports.length) {
                // TODO: link to first port or configured URL
                actions = `<span class="container-link">Open →</span>`;
            }
            html += `
                <div class="container-row">
                    <div class="container-left">
                        <span class="dot ${dotClass}"></span>
                        ${escapeHtml(c.name || c.id)}
                        ${c.health ? `<span class="status-badge ${c.health === "healthy" ? "" : "warning"}">${c.health}</span>` : ""}
                    </div>
                    ${actions}
                </div>
            `;
        });
        body.innerHTML = html;
    } catch (e) {
        body.innerHTML = `<p class="empty-state">Error loading containers.</p>`;
        console.error(e);
    }
}

function closeModal(id) {
    document.getElementById(id).classList.remove("active");
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
}
