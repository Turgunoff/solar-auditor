# Deploy — VPS + Docker Compose + GitHub Actions

One repo is enough: `ci.yml` tests on every push. Deploy is manual
(`git pull` on the server) — no auto-deploy by decision.

## Server map (51.12.209.235, user `ozodbek`)

| What | Where |
|---|---|
| Repo checkout | `/opt/solar-auditor` (branch `main`) |
| Secrets | `/opt/solar-auditor/.env` (gitignored, on server only) |
| Generated data | `/opt/solar-auditor/backend/static` (uploads/renders/exports, survives redeploys) |
| systemd unit | `solar-auditor.service` → `docker compose up -d` in `/opt/solar-auditor` (enabled) |
| Host nginx vhost | `/etc/nginx/sites-{available,enabled}/cyberpitch.uz` → `127.0.0.1:8080` |
| Public URL | `http://51.12.209.235:8080` now; `https://cyberpitch.uz` after DNS + certbot |
| SSH key (local) | `Downloads/iMe Desktop/ozodbek_key.pem` on the dev machine |

Taken host ports (do not use): `80` (main site nginx), `8000` (quizin app).

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
curl http://localhost:8080/api/v1/health
```

Note: host ports 80 (main site nginx) and 8000 (another app) are taken,
so the app serves on **8080**.

## Domain (cyberpitch.uz) — done on server

Host nginx vhost `/etc/nginx/sites-{available,enabled}/cyberpitch.uz`
proxies `cyberpitch.uz` + `www` → `127.0.0.1:8080`. Verified with
`Host:` header override (200 + live `/api/v1/health`).

After DNS points at the server IP:

```bash
sudo certbot --nginx -d cyberpitch.uz -d www.cyberpitch.uz
```

## Manual update (git pull workflow)

```bash
cd /opt/solar-auditor
git pull origin main
docker compose up -d --build
```

Uploads/renders/exports survive redeploys via the `./backend/static` volume.
