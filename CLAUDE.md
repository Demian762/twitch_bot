# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BotDelEstadio** is a Twitch chatbot for the "Hablemos de Pavadas" channel, built with `twitchio`. It includes a points system backed by Google Sheets, minigames, audio playback, API integrations, and a parallel Telegram bot.

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

1. `utils/secretos.py` (gitignored) with `kick_client_id` / `kick_client_secret` / `kick_redirect_uri` — same values as the other machines, it's the same registered Kick app.
2. `cloudflared` installed: `winget install --id Cloudflare.cloudflared`.
3. The **same Cloudflare Tunnel identity** copied into `%USERPROFILE%\.cloudflared\` on the new machine: `cert.pem`, `<tunnel-id>.json`, and `config.yml`. Without this the machine can't authenticate as the `kickbot` tunnel — copy the whole folder from a working machine rather than re-running `cloudflared tunnel login`/`create` (that would make a second, redundant tunnel).
4. Either copy `.kick.tokens.json` from a working machine, or run `python -m utils.kick.authorize` again on the new one (same Kick account, fine to re-authorize).

The Kick app's Webhook URL (`https://kickbot.hablemosdepavadas.com.ar/kick/webhook`, panel at kick.com/settings/developer) is configured once for the app as a whole — it doesn't need to change per machine, since the tunnel always forwards to whichever machine currently has `cloudflared tunnel run kickbot` running.

## Key Files

| File | Role |
|------|------|
| [utils/configuracion.py](utils/configuracion.py) | Central config: admins, social links, spam messages, grog texts, insult dictionary, trivia questions, routine timers |
| [utils/secretos.py](utils/secretos.py) | All API credentials — **gitignored**, must exist locally |
| [utils/bot_config.py](utils/bot_config.py) | `BotConfig`, `APIManager`, `BotState` class definitions |
| [utils/puntitos_manager.py](utils/puntitos_manager.py) | Google Sheets read/write for the points system |
| [utils/api_games.py](utils/api_games.py) | RAWG.io and Steam API wrappers |
| [utils/logger.py](utils/logger.py) | Logging setup (daily files in `/logs/`) |
| [bot_del_estadio.spec](bot_del_estadio.spec) | PyInstaller spec: bundles ffmpeg.exe and `storage/` audio files |
| [bot_del_estadio_kick.py](bot_del_estadio_kick.py) | Kick entrypoint (`KickBot`) — see "Kick integration" above |
| [utils/kick/](utils/kick/) | Kick OAuth, REST client, webhook server, command dispatcher |
| [bot_launcher.pyw](bot_launcher.pyw) | Tkinter launcher UI — Twitch/Kick switch, start/stop, audio/voice/metrics/emoji toggles |

## Points System

Points ("puntitos") are stored in a Google Sheet. The spreadsheet columns are `nombre`, `puntos` (current), and `historico` (lifetime total). Access is via a service account defined in `secretos.py`. Relevant commands: `!consulta`, `!puntos`, `!top`, `!sorteo`.

## Credentials (`utils/secretos.py`)

This file is gitignored. It must contain variables for:
- Twitch OAuth token, client ID, bot user ID
- RAWG API key, Steam API key
- YouTube API key and channel ID
- Telegram bot token
- Google Sheets service account JSON credentials
- Kick app credentials: `kick_client_id`, `kick_client_secret`, `kick_redirect_uri` (from kick.com/settings/developer — see "Kick integration" above)

## Platform Notes

- Audio playback (`winsound`) is **Windows-only**
- The project is built and deployed on Windows; the compiled `.exe` targets Windows
- Logs are written daily to `logs/bot_YYYYMMDD.log`
