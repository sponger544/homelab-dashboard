import aiohttp
import json
import ssl
import os
from typing import Any

class DockerService:
    def __init__(self, config: dict, secrets: dict):
        self.name = config.get("name", "Docker Host")
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 2376)
        self.use_tls = config.get("use_tls", True)
        self.ca_cert = config.get("ca_cert", "")
        self.timeout = aiohttp.ClientTimeout(total=10)

    async def _request(self, path: str) -> Any:
        url = f"https://{self.host}:{self.port}{path}" if self.use_tls else f"http://{self.host}:{self.port}{path}"

        ssl_ctx = None
        if self.use_tls:
            ssl_ctx = ssl.create_default_context()
            ca_path = self.ca_cert if self.ca_cert else "/app/certs/ca.pem"
            if os.path.exists(ca_path):
                ssl_ctx.load_verify_locations(ca_path)
            else:
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE

        session = aiohttp.ClientSession(timeout=self.timeout)
        try:
            async with session.get(url, ssl=ssl_ctx) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data if isinstance(data, list) else [data]
                return None
        except Exception:
            return None

    async def get_container_summary(self) -> dict:
        containers = await self._request("/containers/json?all=true")
        if not containers:
            return {
                "name": self.name,
                "total": 0,
                "running": 0,
                "healthy_pct": 0,
                "status": "error",
                "containers": []
            }

        running = 0
        healthy = 0
        healthy_checkable = 0
        container_list = []

        for c in containers:
            name = (c.get("Names") or [None])[0]
            if name:
                name = name.lstrip("/")
            status = c.get("State", "unknown")
            image = c.get("Image", "unknown")

            health = c.get("State", {}).get("Health", {}) or {}
            health_status = health.get("Status", "")

            if status == "running":
                running += 1

            if health_status in ["healthy", "unhealthy"]:
                healthy_checkable += 1
                if health_status == "healthy":
                    healthy += 1

            ports = []
            for p in (c.get("Ports") or []):
                public = p.get("PublicPort")
                if public:
                    ports.append(int(public))

            container_list.append({
                "id": c.get("Id", "")[:12],
                "name": name,
                "image": image,
                "status": status,
                "health": health_status,
                "ports": ports
            })

        healthy_pct = (healthy / healthy_checkable * 100) if healthy_checkable > 0 else (100 if running > 0 else 0)

        return {
            "name": self.name,
            "total": len(containers),
            "running": running,
            "healthy_pct": healthy_pct,
            "status": "ok" if len(containers) > 0 else "error",
            "containers": container_list
        }

    async def test_connection(self) -> bool:
        info = await self._request("/info")
        return isinstance(info, list) and len(info) > 0
