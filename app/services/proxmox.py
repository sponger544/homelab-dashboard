import aiohttp
import json
from typing import Any

class ProxmoxService:
    def __init__(self, config: dict, secrets: dict):
        self.endpoint = config.get("endpoint", "").rstrip("/")
        self.token_id = secrets.get("token_id", "")
        self.token_secret = secrets.get("token_secret", "")
        self.track_vms = config.get("track_vms", True)
        self.track_temps = config.get("track_temps", True)
        self.timeout = aiohttp.ClientTimeout(total=15)

    def _headers(self):
        return {"Authorization": f"PVEAPIToken={self.token_id}={self.token_secret}"}

    async def _request(self, path: str) -> Any:
        url = f"{self.endpoint}/api2/json{path}"
        session = aiohttp.ClientSession(timeout=self.timeout)
        try:
            async with session.get(url, headers=self._headers(), ssl=False) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data")
                return None
        except Exception:
            return None

    async def get_cluster_status(self) -> dict:
        nodes = await self._request("/nodes")
        if not nodes:
            return {"online_nodes": 0, "total_vms": 0, "status": "error"}

        online_nodes = 0
        total_vms = 0
        total_ram_used = 0
        total_ram_max = 0
        total_cpu = 0
        max_cpu = 0
        temps = []
        net_stats = []

        for node in nodes:
            node_name = node.get("node")
            node_status = await self._request(f"/nodes/{node_name}/status")
            if node_status and isinstance(node_status, list):
                info = node_status[0]
                status = info.get("status", "unknown")
                if status == "online":
                    online_nodes += 1
                    total_vms += info.get("vmmax", 0)
                    mem_used = info.get("memory", {}).get("used", 0) or 0
                    mem_max = info.get("memory", {}).get("max", 0) or 1
                    total_ram_used += mem_used
                    total_ram_max += mem_max
                    total_cpu += info.get("cpu", 0) or 0
                    max_cpu += 1

                    temps.append(info.get("temperature", []))

                    net_in = info.get("netin", 0) or 0
                    net_out = info.get("netout", 0) or 0
                    net_stats.append({"in": net_in, "out": net_out})

        avg_cpu = (total_cpu / max_cpu * 100) if max_cpu > 0 else 0
        avg_cpu = min(avg_cpu, 100)
        ram_pct = (total_ram_used / total_ram_max * 100) if total_ram_max > 0 else 0

        avg_temp = 0
        all_temps = []
        for t_list in temps:
            if isinstance(t_list, list):
                for t in t_list:
                    all_temps.append(t)
        if all_temps:
            avg_temp = sum(t.get("value", 0) for t in all_temps) / len(all_temps)

        net_in_total = sum(n["in"] for n in net_stats)
        net_out_total = sum(n["out"] for n in net_stats)
        net_in_mbps = net_in_total / 1000000
        net_out_mbps = net_out_total / 1000000

        return {
            "online_nodes": online_nodes,
            "total_vms": total_vms,
            "cpu_pct": round(avg_cpu, 1),
            "ram_pct": round(ram_pct, 1),
            "ram_used_gb": round(total_ram_used / (1024**3), 1),
            "ram_max_gb": round(total_ram_max / (1024**3), 1),
            "avg_temp": round(avg_temp, 0),
            "net_in_mbps": round(net_in_mbps, 0),
            "net_out_mbps": round(net_out_mbps, 0),
            "status": "ok" if online_nodes > 0 else "error"
        }

    async def get_vms_and_cts(self) -> list:
        vms = await self._request("/cluster/resources?type=vm")
        if not vms or not isinstance(vms, list):
            return []

        result = []
        for vm in vms:
            name = vm.get("name", "Unknown")
            vmid = vm.get("vmid")
            vm_type = "CT" if vm.get("type") == "lxc" else "VM"
            status = vm.get("status", "unknown")
            node = vm.get("node", "unknown")
            cpu = round(vm.get("cpu", 0) or 0, 1)
            mem_used = vm.get("mem", 0) or 0
            mem_max = vm.get("maxmem", 0) or 1
            mem_used_gb = round(mem_used / (1024**3), 1)
            mem_max_gb = round(mem_max / (1024**3), 1)

            result.append({
                "name": name,
                "vmid": vmid,
                "type": vm_type,
                "status": status,
                "node": node,
                "cpu": cpu,
                "mem_used_gb": mem_used_gb,
                "mem_max_gb": mem_max_gb
            })

        return sorted(result, key=lambda x: x["name"].lower())

    async def test_connection(self) -> bool:
        nodes = await self._request("/nodes")
        return isinstance(nodes, list) and len(nodes) > 0
