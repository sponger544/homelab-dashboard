import aiohttp
import json
from typing import Any

class GrafanaService:
    def __init__(self, config: dict, secrets: dict):
        self.url = config.get("url", "").rstrip("/")
        self.api_key = secrets.get("api_key", "")
        self.timeout = aiohttp.ClientTimeout(total=10)

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}"}

    async def _request(self, path: str) -> Any:
        url = f"{self.url}/api{path}"
        session = aiohttp.ClientSession(timeout=self.timeout)
        try:
            async with session.get(url, headers=self._headers()) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                return None
        except Exception:
            return None

    async def get_dashboards(self, limit: int = 10) -> list:
        dashboards = await self._request(f"/search?limit={limit}&type=dash-db&starred=false")
        if not dashboards:
            return []
        return [
            {
                "uid": d.get("uid"),
                "title": d.get("title"),
                "url": f"{self.url}/d/{d.get('uid')}/{d.get('title', '').replace(' ', '-')}"
            }
            for d in dashboards
        ]

    async def test_connection(self) -> bool:
        health = await self._request("/health")
        return health is not None and health.get("database") == "OK"
