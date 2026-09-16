import json
from fastapi import APIRouter, Form
from app.db import get_db, mark_setup_complete

router = APIRouter()

@router.post("/submit")
async def submit_wizard(
    # Proxmox
    proxmox_endpoint: str = Form(""),
    proxmox_token_id: str = Form(""),
    proxmox_token_secret: str = Form(""),
    track_vms: int = Form(1),
    track_temps: int = Form(1),
    # Docker
    docker_hosts_json: str = Form("[]"),
    # Services
    use_grafana: int = Form(0),
    grafana_url: str = Form(""),
    grafana_api_key: str = Form(""),
    use_immich: int = Form(0),
    immich_url: str = Form(""),
    immich_api_key: str = Form(""),
    use_nut: int = Form(0),
    nut_url: str = Form(""),
    nut_device: str = Form("ups"),
    nut_username: str = Form("monuser"),
    nut_password: str = Form("")
):
    try:
        docker_hosts = json.loads(docker_hosts_json)
    except json.JSONDecodeError:
        docker_hosts = []

    async with get_db() as db:
        # Proxmox
        if proxmox_endpoint and proxmox_token_id and proxmox_token_secret:
            config = json.dumps({
                "track_vms": bool(track_vms),
                "track_temps": bool(track_temps)
            })
            secrets = json.dumps({
                "token_id": proxmox_token_id,
                "token_secret": proxmox_token_secret
            })
            await db.execute(
                "INSERT INTO data_sources (type, name, endpoint, config, secret_json) VALUES (?, ?, ?, ?, ?)",
                ("proxmox", "Proxmox Cluster", proxmox_endpoint.rstrip("/"), config, secrets)
            )

        # Docker hosts
        for host in docker_hosts:
            name = host.get("name", "Docker Host")
            host_ip = host.get("host", "")
            port = host.get("port", 2376)
            use_tls = host.get("use_tls", True)
            ca_cert = host.get("ca_cert", "")
            if host_ip:
                config = json.dumps({
                    "name": name,
                    "host": host_ip,
                    "port": int(port),
                    "use_tls": bool(use_tls),
                    "ca_cert": ca_cert
                })
                await db.execute(
                    "INSERT INTO data_sources (type, name, endpoint, config, secret_json) VALUES (?, ?, ?, ?, ?)",
                    ("docker", name, f"https://{host_ip}:{port}" if use_tls else f"http://{host_ip}:{port}", config, "{}")
                )

        # Grafana
        if use_grafana and grafana_url and grafana_api_key:
            config = json.dumps({"url": grafana_url.rstrip("/")})
            secrets = json.dumps({"api_key": grafana_api_key})
            await db.execute(
                "INSERT INTO data_sources (type, name, endpoint, config, secret_json) VALUES (?, ?, ?, ?, ?)",
                ("grafana", "Grafana", grafana_url.rstrip("/"), config, secrets)
            )

        # Immich
        if use_immich and immich_url and immich_api_key:
            config = json.dumps({"url": immich_url.rstrip("/")})
            secrets = json.dumps({"api_key": immich_api_key})
            await db.execute(
                "INSERT INTO data_sources (type, name, endpoint, config, secret_json) VALUES (?, ?, ?, ?, ?)",
                ("immich", "Immich", immich_url.rstrip("/"), config, secrets)
            )

        # NUT
        if use_nut and nut_url:
            config = json.dumps({"url": nut_url.rstrip("/"), "device": nut_device})
            secrets = json.dumps({"username": nut_username, "password": nut_password})
            await db.execute(
                "INSERT INTO data_sources (type, name, endpoint, config, secret_json) VALUES (?, ?, ?, ?, ?)",
                ("nut", "UPS (NUT)", nut_url.rstrip("/"), config, secrets)
            )

        await db.commit()

    await mark_setup_complete()
    return {"ok": True}
