import asyncio
import json
from typing import List
from fastapi import APIRouter, HTTPException
from app.db import get_db, is_setup_complete
from app.services.proxmox import ProxmoxService
from app.services.docker import DockerService
from app.services.grafana import GrafanaService
from app.services.immich import ImmichService
from app.services.nut import NUTService

router = APIRouter()

async def get_services_by_type(service_type: str):
    """Fetch active data sources of a given type."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, name, endpoint, config, secret_json FROM data_sources WHERE type = ? AND is_active = 1",
            (service_type,)
        )
        rows = await cursor.fetchall()
        services = []
        for row in rows:
            config = json.loads(row[3]) if row[3] else {}
            secrets = json.loads(row[4]) if row[4] else {}
            # Merge endpoint into config for service initialization
            config["endpoint"] = row[2]
            config["name"] = row[1]
            services.append({"id": row[0], "config": config, "secrets": secrets})
        return services

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/needs-setup")
async def check_setup():
    complete = await is_setup_complete()
    return {"needs_setup": not complete}

@router.get("/stats")
async def get_stats():
    """Get all stats for the Infrastructure section."""
    result = {
        "proxmox": None,
        "docker_hosts": [],
        "immich": None,
        "nut": None
    }

    # Proxmox
    proxmox_sources = await get_services_by_type("proxmox")
    if proxmox_sources:
        src = proxmox_sources[0]
        svc = ProxmoxService(src["config"], src["secrets"])
        result["proxmox"] = await svc.get_cluster_status()

    # Docker hosts
    docker_sources = await get_services_by_type("docker")
    for src in docker_sources:
        svc = DockerService(src["config"], src["secrets"])
        summary = await svc.get_container_summary()
        result["docker_hosts"].append({
            "id": src["id"],
            **summary
        })

    # Immich
    immich_sources = await get_services_by_type("immich")
    if immich_sources:
        src = immich_sources[0]
        svc = ImmichService(src["config"], src["secrets"])
        result["immich"] = await svc.get_library_stats()

    # NUT
    nut_sources = await get_services_by_type("nut")
    if nut_sources:
        src = nut_sources[0]
        svc = NUTService(src["config"], src["secrets"])
        result["nut"] = await svc.get_status()

    return result

@router.get("/proxmox/vms")
async def get_proxmox_vms():
    """Get VM and CT details from Proxmox."""
    sources = await get_services_by_type("proxmox")
    if not sources:
        return []
    svc = ProxmoxService(sources[0]["config"], sources[0]["secrets"])
    return await svc.get_vms_and_cts()

@router.get("/storage-mounts")
async def get_storage_mounts():
    """Get configured storage mounts (user manages these via admin)."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, host_label, mount_path, filesystem_type FROM storage_mounts WHERE is_active = 1 ORDER BY display_order"
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "host_label": r[1],
                "mount_path": r[2],
                "filesystem_type": r[3]
            }
            for r in rows
        ]

@router.get("/docker/{host_id}/containers")
async def get_docker_containers(host_id: int):
    """Get containers for a specific Docker host (for the modal)."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT name, endpoint, config, secret_json FROM data_sources WHERE id = ? AND type = 'docker' AND is_active = 1",
            (host_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Docker host not found")

        config = json.loads(row[2]) if row[2] else {}
        secrets = json.loads(row[3]) if row[3] else {}
        config["endpoint"] = row[1]
        config["name"] = row[0]
        svc = DockerService(config, secrets)
        summary = await svc.get_container_summary()
        return {
            "host_name": config["name"],
            "containers": summary.get("containers", [])
        }

@router.get("/links/internal")
async def get_internal_links():
    """Get internal links grouped."""
    async with get_db() as db:
        groups = await db.execute(
            "SELECT id, name FROM link_groups WHERE tab = 'internal' AND is_visible = 1 ORDER BY display_order"
        )
        groups_rows = await groups.fetchall()

        result = []
        for gid, gname in groups_rows:
            links = await db.execute(
                "SELECT id, name, url, icon_type, icon_value FROM links WHERE group_id = ? AND is_visible = 1 ORDER BY display_order",
                (gid,)
            )
            links_rows = await links.fetchall()
            if links_rows:
                result.append({
                    "group": gname,
                    "links": [
                        {
                            "id": r[0],
                            "name": r[1],
                            "url": r[2],
                            "icon_type": r[3],
                            "icon_value": r[4]
                        }
                        for r in links_rows
                    ]
                })
        return result

@router.get("/links/external")
async def get_external_links():
    """Get external links grouped."""
    async with get_db() as db:
        groups = await db.execute(
            "SELECT id, name FROM link_groups WHERE tab = 'external' AND is_visible = 1 ORDER BY display_order"
        )
        groups_rows = await groups.fetchall()

        result = []
        for gid, gname in groups_rows:
            links = await db.execute(
                "SELECT id, name, url, icon_type, icon_value FROM links WHERE group_id = ? AND is_visible = 1 ORDER BY display_order",
                (gid,)
            )
            links_rows = await links.fetchall()
            if links_rows:
                result.append({
                    "group": gname,
                    "links": [
                        {
                            "id": r[0],
                            "name": r[1],
                            "url": r[2],
                            "icon_type": r[3],
                            "icon_value": r[4]
                        }
                        for r in links_rows
                    ]
                })
        return result
