# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BotDelEstadio** is a Twitch chatbot for the "Hablemos de Pavadas" channel, built with `twitchio`. It includes a points system backed by Google Sheets, minigames, audio playback, API integrations, and a parallel Telegram bot.

## Running the Bot

```bash
# Activate virtual environment
.\bot-env\Scripts\activate

# Run the bot
python bot_del_estadio.py
```

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

## Points System

Points ("puntitos") are stored in a Google Sheet. The spreadsheet columns are `nombre`, `puntos` (current), and `historico` (lifetime total). Access is via a service account defined in `secretos.py`. Relevant commands: `!consulta`, `!puntos`, `!top`, `!sorteo`.

## Credentials (`utils/secretos.py`)

This file is gitignored. It must contain variables for:
- Twitch OAuth token, client ID, bot user ID
- RAWG API key, Steam API key
- YouTube API key and channel ID
- Telegram bot token
- Google Sheets service account JSON credentials

## Platform Notes

- Audio playback (`winsound`) is **Windows-only**
- The project is built and deployed on Windows; the compiled `.exe` targets Windows
- Logs are written daily to `logs/bot_YYYYMMDD.log`
