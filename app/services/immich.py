import aiohttp
import json
from typing import Any

class ImmichService:
    def __init__(self, config: dict, secrets: dict):
        self.url = config.get("url", "").rstrip("/")
        self.api_key = secrets.get("api_key", "")
        self.timeout = aiohttp.ClientTimeout(total=10)

    def _headers(self):
        return {"x-api-key": self.api_key}

    async def _request(self, path: str) -> Any:
        url = f"{self.url}/api{path}"
        session = aiohttp.ClientSession(timeout=self.timeout)
        try:
            async with session.get(url, headers=self._headers()) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception:
            return None

    async def get_library_stats(self) -> dict:
        stats = await self._request("/statistics")
        if not stats:
            return {"status": "error", "photos": 0, "videos": 0, "usage": 0}

        photos = stats.get("photos", 0) or 0
        videos = stats.get("videos", 0) or 0
        usage_bytes = stats.get("usage", 0) or 0

        return {
            "status": "ok",
            "photos": photos,
            "videos": videos,
            "total": photos + videos,
            "usage_gb": round(usage_bytes / (1024**3), 1)
        }

    async def test_connection(self) -> bool:
        stats = await self._request("/statistics")
        return stats is not None
