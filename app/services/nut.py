import aiohttp
import json
from typing import Any

class NUTService:
    def __init__(self, config: dict, secrets: dict):
        self.url = config.get("url", "").rstrip("/")
        self.device = config.get("device", "ups")
        self.username = secrets.get("username", "monuser")
        self.password = secrets.get("password", "")
        self.timeout = aiohttp.ClientTimeout(total=8)

    async def _request(self, path: str) -> Any:
        url = f"{self.url}{path}"
        session = aiohttp.ClientSession(timeout=self.timeout)
        try:
            auth = aiohttp.BasicAuth(self.username, self.password)
            async with session.get(url, auth=auth) as resp:
                if resp.status == 200:
                    return await resp.text()
                return None
        except Exception:
            return None

    async def get_status(self) -> dict:
        xml = await self._request(f"/ups/{self.device}")
        if not xml or "<?xml" not in xml:
            return {"status": "error"}

        # Simple XML parsing for upsxmld output
        def get_var(name):
            start = xml.find(f'VALUE="{name}">')
            if start == -1:
                return None
            start = xml.find(">", start) + 1
            end = xml.find("</value", start)
            return xml[start:end].strip() if end > start else None

        battery_charge = get_var("battery.charge")
        ups_status = get_var("ups.status")
        battery_runtime = get_var("battery.runtime")
        input_voltage = get_var("input.voltage")
        ups_load = get_var("ups.load")
        output_power = get_var("ups.realpower") or get_var("ups.power")

        result = {"status": "ok"}

        if battery_charge:
            try:
                result["battery_charge"] = int(battery_charge)
            except ValueError:
                result["battery_charge"] = 0

        if ups_status:
            result["ups_status"] = ups_status

        if battery_runtime:
            try:
                result["runtime_minutes"] = int(battery_runtime)
            except ValueError:
                result["runtime_minutes"] = 0

        if input_voltage:
            result["input_voltage"] = input_voltage

        if ups_load:
            result["ups_load"] = ups_load

        if output_power:
            try:
                result["real_power_w"] = int(float(output_power))
            except ValueError:
                result["real_power_w"] = 0

        return result

    async def test_connection(self) -> bool:
        xml = await self._request(f"/ups/{self.device}")
        return xml is not None and "<?xml" in xml
