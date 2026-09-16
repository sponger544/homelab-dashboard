import json
import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from app.db import get_db, init_db

router = APIRouter()

@router.get("/data-sources")
async def list_data_sources():
    """List all data sources (without full secrets for safety)."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, type, name, endpoint, config, is_active FROM data_sources ORDER BY type, name"
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "type": r[1],
                "name": r[2],
                "endpoint": r[3],
                "config": json.loads(r[4]) if r[4] else {},
                "is_active": bool(r[5])
            }
            for r in rows
        ]

@router.post("/data-sources")
async def create_data_source(
    type: str = Form(...),
    name: str = Form(...),
    endpoint: str = Form(...),
    config_json: str = Form("{}"),
    secret_json: str = Form("{}")
):
    """Create a new data source."""
    try:
        config = json.loads(config_json)
        secrets = json.loads(secret_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO data_sources (type, name, endpoint, config, secret_json) VALUES (?, ?, ?, ?, ?)",
            (type, name, endpoint, config_json, secret_json)
        )
        await db.commit()
        return {"id": cursor.lastrowid}

@router.put("/data-sources/{source_id}")
async def update_data_source(
    source_id: int,
    type: str = Form(...),
    name: str = Form(...),
    endpoint: str = Form(...),
    config_json: str = Form("{}"),
    secret_json: str = Form("{}"),
    is_active: int = Form(1)
):
    try:
        config = json.loads(config_json)
        secrets = json.loads(secret_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    async with get_db() as db:
        await db.execute(
            "UPDATE data_sources SET type=?, name=?, endpoint=?, config=?, secret_json=?, is_active=? WHERE id=?",
            (type, name, endpoint, config_json, secret_json, is_active, source_id)
        )
        await db.commit()
    return {"ok": True}

@router.delete("/data-sources/{source_id}")
async def delete_data_source(source_id: int):
    async with get_db() as db:
        await db.execute("DELETE FROM data_sources WHERE id=?", (source_id,))
        await db.commit()
    return {"ok": True}

@router.post("/data-sources/{source_id}/toggle")
async def toggle_data_source(source_id: int):
    async with get_db() as db:
        await db.execute(
            "UPDATE data_sources SET is_active = NOT is_active WHERE id=?",
            (source_id,)
        )
        await db.commit()
    return {"ok": True}

@router.get("/storage-mounts")
async def list_storage_mounts():
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, data_source_id, host_label, mount_path, filesystem_type, display_order, is_active FROM storage_mounts ORDER BY display_order"
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "data_source_id": r[1],
                "host_label": r[2],
                "mount_path": r[3],
                "filesystem_type": r[4],
                "display_order": r[5],
                "is_active": bool(r[6])
            }
            for r in rows
        ]

@router.post("/storage-mounts")
async def create_storage_mount(
    data_source_id: int = Form(None),
    host_label: str = Form(...),
    mount_path: str = Form(...),
    filesystem_type: str = Form("auto"),
    display_order: int = Form(0)
):
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO storage_mounts (data_source_id, host_label, mount_path, filesystem_type, display_order) VALUES (?, ?, ?, ?, ?)",
            (data_source_id or None, host_label, mount_path, filesystem_type, display_order)
        )
        await db.commit()
        return {"id": cursor.lastrowid}

@router.put("/storage-mounts/{mount_id}")
async def update_storage_mount(
    mount_id: int,
    host_label: str = Form(...),
    mount_path: str = Form(...),
    filesystem_type: str = Form("auto"),
    display_order: int = Form(0),
    is_active: int = Form(1)
):
    async with get_db() as db:
        await db.execute(
            "UPDATE storage_mounts SET host_label=?, mount_path=?, filesystem_type=?, display_order=?, is_active=? WHERE id=?",
            (host_label, mount_path, filesystem_type, display_order, is_active, mount_id)
        )
        await db.commit()
    return {"ok": True}

@router.delete("/storage-mounts/{mount_id}")
async def delete_storage_mount(mount_id: int):
    async with get_db() as db:
        await db.execute("DELETE FROM storage_mounts WHERE id=?", (mount_id,))
        await db.commit()
    return {"ok": True}

@router.get("/link-groups")
async def list_link_groups():
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, name, tab, display_order, is_visible FROM link_groups ORDER BY tab, display_order"
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "tab": r[2],
                "display_order": r[3],
                "is_visible": bool(r[4])
            }
            for r in rows
        ]

@router.post("/link-groups")
async def create_link_group(name: str = Form(...), tab: str = Form("internal"), display_order: int = Form(0)):
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO link_groups (name, tab, display_order) VALUES (?, ?, ?)",
            (name, tab, display_order)
        )
        await db.commit()
        return {"id": cursor.lastrowid}

@router.put("/link-groups/{group_id}")
async def update_link_group(
    group_id: int,
    name: str = Form(...),
    tab: str = Form("internal"),
    display_order: int = Form(0),
    is_visible: int = Form(1)
):
    async with get_db() as db:
        await db.execute(
            "UPDATE link_groups SET name=?, tab=?, display_order=?, is_visible=? WHERE id=?",
            (name, tab, display_order, is_visible, group_id)
        )
        await db.commit()
    return {"ok": True}

@router.delete("/link-groups/{group_id}")
async def delete_link_group(group_id: int):
    async with get_db() as db:
        await db.execute("DELETE FROM link_groups WHERE id=?", (group_id,))
        await db.commit()
    return {"ok": True}

@router.get("/links")
async def list_links(group_id: int = None):
    async with get_db() as db:
        if group_id:
            cursor = await db.execute(
                "SELECT l.id, l.group_id, l.name, l.url, l.icon_type, l.icon_value, l.display_order, l.is_visible, g.name as group_name FROM links l JOIN link_groups g ON l.group_id = g.id WHERE l.group_id = ? ORDER BY l.display_order",
                (group_id,)
            )
        else:
            cursor = await db.execute(
                "SELECT l.id, l.group_id, l.name, l.url, l.icon_type, l.icon_value, l.display_order, l.is_visible, g.name as group_name FROM links l JOIN link_groups g ON l.group_id = g.id ORDER BY g.display_order, l.display_order"
            )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "group_id": r[1],
                "group_name": r[8],
                "name": r[2],
                "url": r[3],
                "icon_type": r[4],
                "icon_value": r[5],
                "display_order": r[6],
                "is_visible": bool(r[7])
            }
            for r in rows
        ]

@router.post("/links")
async def create_link(
    group_id: int = Form(...),
    name: str = Form(...),
    url: str = Form(...),
    icon_type: str = Form("emoji"),
    icon_value: str = Form("🔗"),
    display_order: int = Form(0)
):
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO links (group_id, name, url, icon_type, icon_value, display_order) VALUES (?, ?, ?, ?, ?, ?)",
            (group_id, name, url, icon_type, icon_value, display_order)
        )
        await db.commit()
        return {"id": cursor.lastrowid}

@router.put("/links/{link_id}")
async def update_link(
    link_id: int,
    group_id: int = Form(...),
    name: str = Form(...),
    url: str = Form(...),
    icon_type: str = Form("emoji"),
    icon_value: str = Form("🔗"),
    display_order: int = Form(0),
    is_visible: int = Form(1)
):
    async with get_db() as db:
        await db.execute(
            "UPDATE links SET group_id=?, name=?, url=?, icon_type=?, icon_value=?, display_order=?, is_visible=? WHERE id=?",
            (group_id, name, url, icon_type, icon_value, display_order, is_visible, link_id)
        )
        await db.commit()
    return {"ok": True}

@router.delete("/links/{link_id}")
async def delete_link(link_id: int):
    async with get_db() as db:
        await db.execute("DELETE FROM links WHERE id=?", (link_id,))
        await db.commit()
    return {"ok": True}

@router.post("/icons/upload")
async def upload_icon(file: UploadFile = File(...)):
    """Upload a custom icon."""
    icons_dir = "/app/uploads/icons"
    os.makedirs(icons_dir, exist_ok=True)

    # Sanitize filename
    ext = os.path.splitext(file.filename)[1] or ".png"
    filename = f"icon_{os.urandom(8).hex()}{ext}"
    filepath = os.path.join(icons_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    return {"filename": filename}

@router.get("/icons/{filename}")
async def get_icon(filename: str):
    """Serve an uploaded icon."""
    filepath = os.path.join("/app/uploads/icons", filename)
    if os.path.exists(filepath):
        return FileResponse(filepath)
    raise HTTPException(status_code=404, detail="Icon not found")

@router.post("/icons/fetch-from-url")
async def fetch_icon_from_url(url: str = Form(...)):
    """Download an icon from a URL and save it."""
    import aiohttp
    icons_dir = "/app/uploads/icons"
    os.makedirs(icons_dir, exist_ok=True)

    filename = f"icon_{os.urandom(8).hex()}.png"
    filepath = os.path.join(icons_dir, filename)

    session = aiohttp.ClientSession()
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                content = await resp.read()
                with open(filepath, "wb") as f:
                    f.write(content)
                return {"filename": filename}
            raise HTTPException(status_code=400, detail="Failed to fetch icon")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/docker-url-overrides")
async def create_docker_url_override(
    data_source_id: int = Form(...),
    container_id: str = Form(...),
    custom_url: str = Form(...),
    display_name: str = Form("")
):
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO docker_url_overrides (data_source_id, container_id, custom_url, display_name) VALUES (?, ?, ?, ?)",
            (data_source_id, container_id, custom_url, display_name)
        )
        await db.commit()
    return {"ok": True}

@router.delete("/docker-url-overrides/{override_id}")
async def delete_docker_url_override(override_id: int):
    async with get_db() as db:
        await db.execute("DELETE FROM docker_url_overrides WHERE id=?", (override_id,))
        await db.commit()
    return {"ok": True}

@router.get("/docker-url-overrides")
async def list_docker_url_overrides():
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT o.id, o.data_source_id, o.container_id, o.custom_url, o.display_name, d.name as host_name FROM docker_url_overrides o JOIN data_sources d ON o.data_source_id = d.id"
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "data_source_id": r[1],
                "container_id": r[2],
                "custom_url": r[3],
                "display_name": r[4],
                "host_name": r[5]
            }
            for r in rows
        ]

@router.post("/init-db")
async def initialize_db():
    """Initialize the database schema."""
    await init_db()
    return {"ok": True}
