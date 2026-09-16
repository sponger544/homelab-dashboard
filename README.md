# Home Lab Dashboard

A self-hosted dashboard for monitoring your homelab infrastructure and managing service links — no YAML editing required.

## Features

- **Setup wizard** on first run — configure everything via the web UI
- **Proxmox integration** — VM/CT status, CPU/RAM usage, temperatures, network stats
- **Docker monitoring** — container status from multiple hosts
- **Immich integration** — library stats (photos, videos, storage)
- **NUT/UPS integration** — battery status, real power usage, runtime
- **Grafana integration** — connect for future embedded dashboards
- **Link management** — internal/external links, custom groups, custom icons (emoji, URL, or uploaded)
- **Storage mounts** — track ZFS/Btrfs/ext4 pools
- **SQLite backend** — all configuration stored in a local database
- **Zero config files** — everything managed through the admin panel

## Quick Start

### Build and run

```bash
docker compose up -d --build
```

Open `http://localhost:8080` — the setup wizard will guide you through configuring data sources.

### Prerequisites

For full functionality you'll need:

1. **Proxmox** — create an API token: Datacenter → Permissions → API Tokens
2. **Docker** — configure Remote API on each host (port 2376 with TLS recommended)
3. **Immich** — create an API key in User Settings → API Keys
4. **NUT** — enable `upsxmld` and configure auth in `upsd.users`

### Docker TLS certificates

If your Docker hosts use TLS (recommended), mount the CA cert into the container:

```yaml
volumes:
  - /path/to/docker/certs:/app/certs:ro
```

Then configure the Docker host endpoint in the wizard/admin to use TLS.

## Architecture

- **FastAPI** backend with aiohttp for async API calls
- **SQLite** database (WAL mode) for all configuration
- **Jinja2** templates + vanilla JS frontend
- **Single container** deployment via Docker Compose

## API Endpoints

- `GET /api/health` — Health check
- `GET /api/stats/stats` — All infrastructure stats
- `GET /api/stats/proxmox/vms` — VM/CT details
- `GET /api/stats/docker/{id}/containers` — Container list
- `GET /api/stats/links/internal` — Internal links
- `GET /api/stats/links/external` — External links
- `POST /api/wizard/submit` — Setup wizard submission
- `GET/POST/PUT/DELETE /api/admin/*` — Admin CRUD operations

## Security Notes

- This dashboard is meant to sit behind your existing auth/reverse proxy (TinyAuth, Cloudflare Tunnel, etc.)
- API tokens and secrets are stored in the SQLite database
- Docker connections use TLS when configured
- Proxmox connections use API tokens (not passwords)

## License

MIT
