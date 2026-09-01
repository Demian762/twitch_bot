# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BotDelEstadio** is a Twitch chatbot for the "Hablemos de Pavadas" channel, built with `twitchio`. It includes a points system backed by Cloudflare D1, minigames, audio playback, API integrations, and a parallel Telegram bot.

## Running the Bot

```bash
# Activate virtual environment
.\bot-env\Scripts\activate

# Run the bot (Twitch)
python bot_del_estadio.py

# Run the bot (Kick)
python bot_del_estadio_kick.py
```

`bot_launcher.pyw` is the normal way to run either: it has a Twitch/Kick switch (disabled while a bot is running) and launches the matching script as a subprocess.

## Compiling to Executable

```bash
python utils/compile_bot.py
# Output: dist/bot_del_estadio_YYYY-MM-DD.exe
```

**Before compiling**, apply this manual fix to the Steam API package:
- File: `bot-env/Lib/site-packages/steam_web_api/_version.py` (lines 18-19)
- Change `except Exception: pass` → `except Exception: __version__ = "2.0.4"`

The compile script auto-updates `BUILD_DATE` in `utils/configuracion.py`.

## Architecture

The main bot class in [bot_del_estadio.py](bot_del_estadio.py) extends `twitchio.ext.commands.Bot` and loads three shared state objects plus all command components at startup:

- **`BotConfig`** — weekly schedule, spit-game restrictions, basic config flags
- **`APIManager`** — wraps RAWG, Steam, YouTube, and DolarAPI clients
- **`BotState`** — runtime state: grog counter, active users, minigame state, trivia state

All commands are implemented as **TwitchIO V3 `Component`s** in `commands/` and loaded dynamically via `commands/__init__.py`. Each component receives the shared state objects via its constructor. Adding a new command module means creating a component class (inheriting from `BaseCommand(commands.Component)`) and registering it with `add_component` in `commands/__init__.py`.

A `TelegramVoiceBot` runs concurrently via `asyncio`, listening on Telegram and playing audio locally via `winsound`.

### Kick integration

[bot_del_estadio_kick.py](bot_del_estadio_kick.py) is a second entrypoint that runs the same channel on Kick. It does **not** use twitchio at all — Kick's public API has no persistent-connection option (unlike Twitch's EventSub WebSocket), only webhook push, so the architecture is different under the hood while reusing all the same business logic:

- `utils/kick/dispatcher.py` instantiates the same `commands.COGS` classes and calls the real `Command.callback` behind each `@commands.command` directly (bypassing twitchio's routing, which is hard-coupled to its own `ChatMessage`/`Context` models). `KickContext` (`utils/kick/context.py`) is a minimal duck-type exposing only `.author.name` / `.message.text` / `.send()` — the entire surface the ~52 commands actually touch.
- `utils/kick/auth.py` — OAuth 2.1 + PKCE against `id.kick.com`. Run once per machine: `python -m utils.kick.authorize` (opens a browser, saves tokens to `.kick.tokens.json`).
- `utils/kick/client.py` — REST calls against `api.kick.com/public/v1` (send message, subscribe events, channel/user info, public key).
- `utils/kick/webhook_server.py` — aiohttp server receiving Kick's webhook events, verifying the RSA-SHA256 signature.
- Kick has no persistent connection, so it must be reachable from the public internet: `KickBot` spawns `cloudflared tunnel run kickbot` itself (see "Kick — setting up a new machine" below).
- `utils/mensaje.py`'s `mensaje()` keeps its exact signature for both platforms — `set_broadcaster()` (Twitch) / `set_kick_sender()` (Kick) pick which backend it dispatches to.

Known gaps vs. Twitch: no raid-equivalent event on Kick, no Kick emote overlay, no reconnect watchdog (not needed the same way — chat arrives via webhook, not a persistent connection that can silently die).

#### Kick — setting up a new machine

Beyond the normal environment setup, each machine that will run the Kick bot needs:

1. `.remote_key` (gitignored, repo root) — same as any other machine (see "Remote secrets" above). Once set, `utils/secretos.py` gets `kick_client_id` / `kick_client_secret` / `kick_redirect_uri` / `kick_cloudflare_cert_pem` / `kick_cloudflare_tunnel_credentials` from the secrets worker automatically — same values everywhere, since it's the same registered Kick app and the same Cloudflare Tunnel identity.
2. `cloudflared` — no need to install it by hand: `bot_launcher.pyw` detects it's missing on startup and installs it via winget itself (`CloudflaredInstallWindow`), before opening the launcher.
3. The Cloudflare Tunnel's local files (`~/.cloudflared/cert.pem`, `<tunnel-id>.json`, `config.yml`) — no need to copy that folder by hand either: `utils/kick/tunnel_setup.py` regenerates whichever of those three files are missing from the `kick_cloudflare_*` values in `secretos.py`, the first time `bot_del_estadio_kick.py` starts on that machine. Idempotent — leaves existing files alone.
4. Tokens: either copy `.kick.tokens.json` from a working machine, or do nothing — `get_access_token()` (`utils/kick/auth.py`) opens the browser and runs the authorization flow itself the first time the bot starts without that file (same as running `python -m utils.kick.authorize` manually, just automatic). Either way requires `.remote_key` to already be in place so `secretos.py` gets generated with the Kick credentials.

The Kick app's Webhook URL (`https://kickbot.hablemosdepavadas.com.ar/kick/webhook`, panel at kick.com/settings/developer) is configured once for the app as a whole — it doesn't need to change per machine, since the tunnel always forwards to whichever machine currently has `cloudflared tunnel run kickbot` running.

## Key Files

| File | Role |
|------|------|
| [utils/configuracion.py](utils/configuracion.py) | Central config: admins, social links, spam messages, grog texts, insult dictionary, trivia questions, routine timers |
| [utils/secretos.py](utils/secretos.py) | All API credentials — **gitignored**, regenerated on every startup by `utils/secrets_bootstrap.py` (see "Remote secrets" below) |
| [utils/secrets_bootstrap.py](utils/secrets_bootstrap.py) | Fetches secrets from the Cloudflare secrets worker using `.remote_key` and writes `utils/secretos.py` |
| [utils/bot_config.py](utils/bot_config.py) | `BotConfig`, `APIManager`, `BotState` class definitions |
| [utils/puntitos_manager.py](utils/puntitos_manager.py) | Points system logic — reads/writes Cloudflare D1 via `utils/d1_client.py` |
| [utils/d1_client.py](utils/d1_client.py) | HTTP client for the puntitos Cloudflare Worker (`cloudflare/worker/`) |
| [cloudflare/](cloudflare/) | Two Cloudflare Workers: `worker/` (D1-backed puntitos/victorias/programación API) and `secrets-worker/` (remote secrets API) — see "Remote secrets" below |
| [utils/api_games.py](utils/api_games.py) | RAWG.io and Steam API wrappers |
| [utils/logger.py](utils/logger.py) | Logging setup (daily files in `/logs/`) |
| [bot_del_estadio.spec](bot_del_estadio.spec) | PyInstaller spec: bundles ffmpeg.exe and `storage/` audio files |
| [bot_del_estadio_kick.py](bot_del_estadio_kick.py) | Kick entrypoint (`KickBot`) — see "Kick integration" above |
| [utils/kick/](utils/kick/) | Kick OAuth, REST client, webhook server, command dispatcher |
| [bot_launcher.pyw](bot_launcher.pyw) | Tkinter launcher UI — Twitch/Kick switch, start/stop, audio/voice/metrics/emoji toggles |

## Points System

Points ("puntitos") live in a Cloudflare D1 database (`botdelestadio_db`), accessed through `cloudflare/worker/` (`utils/d1_client.py` is the Python HTTP client). Tables: `puntitos` (`nombre`, `puntos` current, `historico` lifetime), `victorias`, `programacion`, `restricciones_escupir`, `daddy_points`, `claude_memoria`. Relevant commands: `!consulta`, `!puntos`, `!top`, `!sorteo`.

The Google Sheet that originally backed this is retired — D1 is the only source of truth, read and written directly by the Worker.

## Remote secrets

`utils/secretos.py` is gitignored and **generated at every startup**, not hand-authored: `bot_del_estadio.py` / `bot_del_estadio_kick.py` / `utils/kick/authorize.py` all call `ensure_secretos()` (`utils/secrets_bootstrap.py`) before any other `utils` import. It reads a bearer token from `.remote_key` (gitignored, repo root), fetches all credentials as JSON from the dedicated `cloudflare/secrets-worker/` Worker, and writes them out as `utils/secretos.py`. No network/invalid key means the bot refuses to start — there's no offline fallback by design.

To update a credential: edit `utils/secretos.py` locally, run `python cloudflare/push_secrets.py`, review the generated `cloudflare/secrets-worker/seed.sql`, then apply it with `wrangler d1 execute botdelestadio_secrets --remote --file=seed.sql`. Every machine picks up the change on its next start — no need to touch each install by hand.

`installer.py` asks for `.remote_key` directly (pasted in) instead of a `secretos.py` file, since the repo is public and the key must never be committed.

## Credentials (`utils/secretos.py`)

Populated remotely (see "Remote secrets" above). Variables it must contain:
- Twitch OAuth token, client ID, bot user ID
- RAWG API key, Steam API key
- YouTube API key and channel ID
- Telegram bot token
- Google Sheets service account JSON credentials (legacy, kept for now but no longer read by any script)
- Cloudflare D1 worker URL/token (`d1_worker_url`, `d1_worker_token`)
- Kick app credentials: `kick_client_id`, `kick_client_secret`, `kick_redirect_uri` (from kick.com/settings/developer — see "Kick integration" above)

## Platform Notes

- Audio playback (`winsound`) is **Windows-only**
- The project is built and deployed on Windows; the compiled `.exe` targets Windows
- Logs are written daily to `logs/bot_YYYYMMDD.log`
