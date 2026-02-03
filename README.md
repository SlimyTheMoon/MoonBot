# MoonBot - PoB goods monitor for Discord 🚀

A lightweight Discord bot + web dashboard that polls a Path of Building (PoB) goods API, detects health drops and newly published public items, and posts rich alerts to configured channels.

---

## Key features ✅
- Polls a PoB goods API and detects important changes (health drops, new public items)
- Sends embed alerts to configured Discord channels
- Simple web dashboard (Quart) to choose alert channel per guild
- Slash commands: `/set_alert` and `/check_now`
- SQLite persistence (`moonbot.db`) — no external DB required
- Docker-ready (dashboard on port `5000`)

---

## Quick start (local) — 3 steps 💡
1. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

2. Set your Discord token and run:

```powershell
$env:DISCORD_TOKEN = "<your_token>"
python moonbot.py
```

3. Open the dashboard: http://localhost:5000 — select a channel to receive alerts.

---

## Docker
Build:

```bash
docker build -t moonbot:latest .
```

Run (persist DB):

```powershell
docker run -d -e DISCORD_TOKEN="<your_token>" -p 5000:5000 -v %CD%/moonbot.db:/app/moonbot.db --name moonbot moonbot:latest
```

Docker Compose example:

```yaml
version: '3.8'
services:
  moonbot:
    build: .
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
    ports:
      - "5000:5000"
    volumes:
      - ./moonbot.db:/app/moonbot.db
```

---

## Configuration
- Required: `DISCORD_TOKEN` (env var)
- Configurable in `moonbot.py` (top of file):
  - `API_URL` — endpoint to poll
  - `POLL_INTERVAL` — seconds between polls (default: `60`)
  - `DB_NAME` — SQLite filename (default: `moonbot.db`)

Tip: Consider making `API_URL` and `POLL_INTERVAL` env-configurable for production.

---

## Usage (Discord)
- Invite the bot with scopes: `bot`, `applications.commands` and permissions: View Channels, Send Messages, Embed Links
- Slash commands:
  - `/set_alert <channel>` - (admin only) set alerts channel
  - `/check_now` - force immediate API check

---

## Troubleshooting ⚠️
- "Error: DISCORD_TOKEN environment variable is missing." — set `DISCORD_TOKEN` before running.
- Bot not sending messages: ensure it has permission to send embeds in the configured channel.
- Dashboard shows no servers: the bot must be invited to at least one guild and be fully started.

---

## For contributors ✨
- Main logic: `MoonBot.check_pob_data()` in `moonbot.py` (polling + DB diffing)
- Web UI: `templates/index.html` (Quart + Jinja2)
- Suggestions: make API endpoint configurable, add unit tests for parsing/DB, expose `/status` endpoint

---

## License
No license file included - add a `LICENSE` (MIT recommended) to publish this repository.

---

If you'd like, I can also:
1. Open a PR with this change (create branch, commit, push). ✅
2. Convert `API_URL` and `POLL_INTERVAL` to environment variables and update the README. 💡

Tell me which follow-up you want.
