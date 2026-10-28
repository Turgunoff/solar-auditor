# Deploy — VPS + Docker Compose + GitHub Actions

One repo is enough: `ci.yml` tests, `deploy.yml` ships both services.
No separate repo needed.

## Server prep (once)

```bash
# Docker + compose plugin, then:
sudo mkdir -p /opt/solar-auditor
sudo chown $USER /opt/solar-auditor
cd /opt/solar-auditor
git clone https://github.com/Turgunoff/solar-auditor.git .
```

Create `/opt/solar-auditor/.env` on the server (never commit it).
Minimum for live mode:

```env
USE_MOCK=false
META_API_KEY=...
ALLOW_MOCK_FALLBACK=true
```

For offline demo: `USE_MOCK=true` and no key needed.
Frontend map key (optional): `VITE_GOOGLE_MAPS_API_KEY` is baked at build
time — for production, pass it as a build arg or set it in GitHub variables.
Without it the map picker stays hidden and presets/uploads still work.

First run:

```bash
docker compose up -d --build
curl http://localhost:8080/api/health
```

Note: host ports 80 (main site nginx) and 8000 (another app) are taken,
so the app serves on **8080**.

## Domain (cyberpitch.uz) — done on server

Host nginx vhost `/etc/nginx/sites-{available,enabled}/cyberpitch.uz`
proxies `cyberpitch.uz` + `www` → `127.0.0.1:8080`. Verified with
`Host:` header override (200 + live `/api/health`).

After DNS points at the server IP:

```bash
sudo certbot --nginx -d cyberpitch.uz -d www.cyberpitch.uz
```

## GitHub secrets (repo → Settings → Secrets → Actions)

| Secret     | Value                          |
|------------|--------------------------------|
| `SSH_HOST` | server IP / hostname           |
| `SSH_USER` | deploy ssh user                |
| `SSH_KEY`  | private key for that user      |
| `SSH_PORT` | optional, default 22           |

On every push to `main`: backend tests + frontend build/test must pass,
then the server pulls, rebuilds, and restarts. Uploads/renders/exports
survive redeploys via the `./backend/static` volume.
