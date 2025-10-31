```
 ____        _   ____       _ _____     _            _ _       
| __ )  ___ | |_|  _ \  ___| | ____|___| |_ __ _  __| (_) ___  
|  _ \ / _ \| __| | | |/ _ \ |  _| / __| __/ _` |/ _` | |/ _ \ 
| |_) | (_) | |_| |_| |  __/ | |___\__ \ || (_| | (_| | | (_) |
|____/ \___/ \__|____/ \___|_|_____|___/\__\__,_|\__,_|_|\___/ 
```

# 🏆 BotDelEstadio - Hablemos de Pavadas 🎮

> *El pináculo de la ingeniería puesta al servicio de.... **pavadas***

¡El bot OFICIAL que hace que el stream sea más divertido! 🚀

> 📋 **Para ver la lista completa de comandos disponibles, consulta [comandos-stream.md](comandos-stream.md)**

---

## 🏗️ **Arquitectura Técnica**

### 📁 **Estructura del Proyecto**
```
twitch_bot/
├── 🤖 bot_del_estadio.py      # Bot principal refactorizado
├── 📦 commands/               # Sistema de comandos modular
│   ├── __init__.py           # Registro automático de cogs
│   ├── base_command.py       # Clase base para comandos
│   ├── basic_commands.py     # Comandos básicos
│   ├── games_commands.py     # Gaming y APIs (RAWG/Steam)
│   ├── points_commands.py    # Sistema de puntitos
│   ├── minigames_commands.py # Minijuegos y competencias
│   ├── timba_commands.py     # Reto de adivinanza de números
│   ├── info_commands.py      # Información del canal
│   ├── youtube_commands.py   # Integración YouTube
│   ├── drink_commands.py     # Sistema de bebidas
│   ├── trivia_commands.py    # Sistema de trivia
│   ├── utility_commands.py   # Utilidades varias
│   └── ... más módulos
├── 🛠️  utils/                 # Utilidades y configuración
│   ├── bot_config.py         # Configuración centralizada
│   ├── logger.py             # Sistema de logging mejorado
│   ├── api_games.py          # Manager de APIs gaming
│   ├── api_youtube.py        # Manager API YouTube
│   ├── wikipedia_api.py      # Manager API Wikipedia
│   ├── puntitos_manager.py   # Gestor de puntitos
│   ├── secretos.py           # Configuración de secrets
│   └── ... más utilidades
├── 🎵 storage/               # Archivos de audio
├── 📊 telegram_bot/          # Integración Telegram completa
│   ├── telegram_voice_bot.py # Bot principal Telegram
│   ├── audio_converter.py    # Conversor de audio
│   └── ffmpeg_manager.py     # Gestor FFmpeg
├── 📋 guia-bot-ejecutable.md # Guía de instalación
└── 📄 requirements.txt       # Dependencias actualizadas
```

### 🔌 **APIs Integradas**
- **🎮 RAWG.io**: Base de datos completa de videojuegos
- **🎮 Steam Web API**: Precios y información detallada de Steam  
- **📺 YouTube Data API v3**: Videos y podcasts del canal (fix aplicado)
- **💰 DolarAPI**: Precio del dólar en tiempo real
- **🤖 Telegram Bot API**: Bot integrado con funcionalidades de voz
- **📊 Google Sheets API**: Gestión de datos y puntitos
- **🔍 HowLongToBeat**: Tiempo de juego de videojuegos
- **📚 Wikipedia API**: Datos curiosos del "¿Sabías que...?" en español

### ⚙️ **Características Técnicas**
- **🐍 Python 3.11+** con entorno virtual
- **🔄 TwitchIO 2.10.0** para integración con Twitch
- **📝 Logging centralizado** con niveles configurables
- **🗂️ Arquitectura modular** de comandos refactorizada
- **⚡ Sistema de caching** para APIs optimizado
- **🛡️ Manejo robusto de errores** mejorado
- **🎵 Reproducción de audio** nativa en Windows
- **🤖 Bot de Telegram integrado** con Python Telegram Bot 20.7
- **📊 Gestión de datos** con Google Sheets API y gspread

---

## 📋 **Instalación y Configuración**
Para instrucciones detalladas de instalación, configuración y uso, consulta la **[Guía de Instalación](guia-bot-ejecutable.md)**.

---

## 🔗 **Fuentes Externas y Créditos**

| Tecnología | Descripción | Link |
|------------|-------------|------|
| **TwitchIO** | Wrapper de la API de Twitch | [🔗 Documentación](https://twitchio.dev/en/stable/index.html) |
| **RAWG.io** | Base de datos de videojuegos | [🔗 API Docs](https://api.rawg.io/docs/) |
| **Steam API** | Conexión con Steam | [🔗 python-steam-api](https://pypi.org/project/python-steam-api/) |
| **YouTube API** | YouTube Data API v3 | [🔗 Getting Started](https://developers.google.com/youtube/v3/getting-started?hl=es-419) |
| **DolarAPI** | Precio del dólar argentino | [🔗 DolarAPI](https://dolarapi.com) |
| **Python Telegram Bot** | Framework para bots de Telegram | [🔗 python-telegram-bot](https://python-telegram-bot.org/) |
| **gspread** | Cliente Python para Google Sheets | [🔗 gspread Docs](https://docs.gspread.org/) |

---

<div align="center">

**🎮 Desarrollado con ❤️ para la comunidad de Hablemos de Pavadas 🎮**

*¿Encontraste un bug? ¿Tenés una idea genial? ¡Abrí un issue!* 

[![Twitch](https://img.shields.io/badge/Twitch-9146FF?style=for-the-badge&logo=twitch&logoColor=white)](https://www.twitch.tv/hablemosdepavadaspod)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com)

</div>