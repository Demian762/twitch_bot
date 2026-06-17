import asyncio
import ctypes
import ctypes.wintypes
import json
import os
import struct
import sys
import time

import aiohttp
import psutil
import pynvml
from aiohttp import web

_OVERLAY_HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { margin:0; padding:0; }
body {
  background: transparent;
  overflow: hidden;
  width: 100vw;
  height: 100vh;
  font-family: "Segoe UI Emoji","Apple Color Emoji","Noto Color Emoji",sans-serif;
}
.emote-item {
  position: fixed;
  width: 100px;
  height: 100px;
  object-fit: contain;
  pointer-events: none;
  animation: moveEmote 6s ease-in-out forwards;
}
@keyframes moveEmote {
  0%   { transform:translate(0,0);                  opacity:0; }
  8%   { transform:translate(0,0);                  opacity:1; }
  85%  { transform:translate(var(--dx),var(--dy));  opacity:1; }
  100% { transform:translate(var(--dx),var(--dy));  opacity:0; }
}
.gif-item {
  position: fixed;
  object-fit: contain;
  animation: gifShow 5s ease forwards;
}
@keyframes gifShow {
  0%   { opacity:0; transform:scale(0.85); }
  10%  { opacity:1; transform:scale(1);    }
  80%  { opacity:1; transform:scale(1);    }
  100% { opacity:0; transform:scale(0.95); }
}
</style>
</head>
<body>
<script>
function spawnEmote(url, delay) {
  setTimeout(function() {
    var img = document.createElement('img');
    img.className = 'emote-item';
    img.src = url;
    var W = window.innerWidth, H = window.innerHeight, s = 100;
    var x0 = Math.random() * (W - s);
    var y0 = Math.random() * (H - s);
    var x1 = Math.random() * (W - s);
    var y1 = Math.random() * (H - s);
    img.style.left = x0 + 'px';
    img.style.top  = y0 + 'px';
    img.style.setProperty('--dx', (x1 - x0) + 'px');
    img.style.setProperty('--dy', (y1 - y0) + 'px');
    document.body.appendChild(img);
    setTimeout(function(){ img.remove(); }, 6400);
  }, delay);
}
function spawnGif(name) {
  var size = Math.round(300 + Math.random() * 400);
  var img = document.createElement('img');
  img.className = 'gif-item';
  img.style.top = '-9999px';
  img.onload = function() {
    if (!img.naturalWidth || !img.naturalHeight) return;
    var rw, rh;
    if (img.naturalWidth >= img.naturalHeight) {
      rw = size; rh = Math.round(size * img.naturalHeight / img.naturalWidth);
      img.style.width = size + 'px'; img.style.height = 'auto';
    } else {
      rh = size; rw = Math.round(size * img.naturalWidth / img.naturalHeight);
      img.style.height = size + 'px'; img.style.width = 'auto';
    }
    img.style.left = Math.random() * Math.max(0, window.innerWidth  - rw) + 'px';
    img.style.top  = Math.random() * Math.max(0, window.innerHeight * 0.8 - rh) + 'px';
  };
  img.src = '/images/' + name + '.gif';
  document.body.appendChild(img);
  setTimeout(function(){ img.remove(); }, 5200);
}
function connect() {
  var ws = new WebSocket('ws://' + location.host + '/ws/overlay');
  ws.onmessage = function(e) {
    var data = JSON.parse(e.data);
    if (data.type === 'twitch_emote') {
      data.urls.forEach(function(url, i) {
        for (var j = 0; j < 5; j++) { spawnEmote(url, i * 150 + j * 60); }
      });
    } else if (data.type === 'gif') {
      spawnGif(data.name);
    }
  };
  ws.onclose = function() { setTimeout(connect, 2000); };
}
connect();
</script>
</body>
</html>
"""

from utils.logger import logger

# Tipos ctypes para Windows shared memory API (se configuran una vez al importar)
_k32 = ctypes.windll.kernel32
_k32.OpenFileMappingW.restype = ctypes.wintypes.HANDLE
_k32.OpenFileMappingW.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.LPCWSTR]
_k32.MapViewOfFile.restype = ctypes.c_void_p
_k32.MapViewOfFile.argtypes = [
    ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD, ctypes.wintypes.DWORD,
    ctypes.c_size_t,
]
_k32.UnmapViewOfFile.restype = ctypes.wintypes.BOOL
_k32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
_k32.CloseHandle.restype = ctypes.wintypes.BOOL
_k32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]

_FILE_MAP_READ = 0x0004


class GPUCollector:
    def __init__(self):
        try:
            pynvml.nvmlInit()
            self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            self.ok = True
        except Exception as e:
            logger.warning(f"[metrics] GPU no disponible: {e}")
            self.ok = False

    def read(self):
        if not self.ok:
            return None
        try:
            temp = pynvml.nvmlDeviceGetTemperature(self.handle, pynvml.NVML_TEMPERATURE_GPU)
            util = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
            mem = pynvml.nvmlDeviceGetMemoryInfo(self.handle)
            return {
                "temp_c": temp,
                "usage": util.gpu,
                "vram_used_mb": mem.used // (1024 * 1024),
                "vram_total_mb": mem.total // (1024 * 1024),
                "vram_pct": round(mem.used / mem.total * 100, 1),
            }
        except Exception:
            return None


class CPUCollector:
    def __init__(self):
        psutil.cpu_percent(interval=None)  # primera llamada de calentamiento

    def read(self):
        try:
            vm = psutil.virtual_memory()
            return {
                "usage": psutil.cpu_percent(interval=None),
                "ram_used_mb": (vm.total - vm.available) // (1024 * 1024),
                "ram_total_mb": vm.total // (1024 * 1024),
                "ram_pct": vm.percent,
            }
        except Exception:
            return None


class RTSSCollector:
    """Lee FPS desde RTSSSharedMemoryV2. Devuelve None si RTSS no está corriendo.

    Layout de app entry en RTSS 7.3.x:
      +0x000: DWORD processID
      +0x004: CHAR szName[260]
      +0x108: DWORD dwFlags
      +0x10C: DWORD dwTime0  (inicio ventana de medición, ms)
      +0x110: DWORD dwTime1  (fin ventana de medición, ms)
      +0x114: DWORD dwFrames (frames en la ventana)
    """

    # Procesos no-juego que RTSS puede capturar — agregar más según logs
    _EXCLUIDOS = {
        "obs64.exe", "obs.exe", "obs32.exe",
        "obs-browser-page.exe",
        "dwm.exe", "explorer.exe",
        "chrome.exe", "firefox.exe", "msedge.exe",
        "discord.exe", "streamlabs obs.exe",
        "wavelink.exe",           # Elgato Wave Link
        "widgetboard.exe",        # Windows Widgets
        "xboxpcappft.exe",        # Xbox PC App
    }
    _warn_logged = False
    _vistos: set[str] = set()  # para loguear cada proceso nuevo una sola vez

    def read(self):
        try:
            return self._do_read()
        except Exception as e:
            if not RTSSCollector._warn_logged:
                RTSSCollector._warn_logged = True
                logger.warning(f"[metrics] RTSS no disponible: {e}")
            return None

    def _do_read(self):
        h = _k32.OpenFileMappingW(_FILE_MAP_READ, False, "RTSSSharedMemoryV2")
        if not h:
            return None
        try:
            ptr = _k32.MapViewOfFile(h, _FILE_MAP_READ, 0, 0, 28)
            if ptr is None:
                return None
            try:
                header_raw = bytes((ctypes.c_byte * 28).from_address(ptr))
            finally:
                _k32.UnmapViewOfFile(ptr)

            if header_raw[:4] != b"SSTR":  # 'RTSS' como DWORD little-endian
                return None

            app_entry_size, app_arr_offset, app_arr_size = struct.unpack_from("<III", header_raw, 8)
            total_needed = app_arr_offset + app_arr_size * app_entry_size

            ptr2 = _k32.MapViewOfFile(h, _FILE_MAP_READ, 0, 0, total_needed)
            if ptr2 is None:
                return None
            try:
                full = bytes((ctypes.c_byte * total_needed).from_address(ptr2))
            finally:
                _k32.UnmapViewOfFile(ptr2)

            best_fps = None
            for i in range(app_arr_size):
                base = app_arr_offset + i * app_entry_size
                pid = struct.unpack_from("<I", full, base)[0]
                if pid == 0:
                    continue

                # Nombre del proceso (null-terminated, 260 bytes en +0x004)
                # Puede venir con ruta completa — usamos solo el basename
                name_raw = full[base + 4:base + 4 + 260]
                name = name_raw.split(b'\x00')[0].decode('ascii', errors='replace')
                basename = name.split('\\')[-1].split('/')[-1]

                if name not in RTSSCollector._vistos:
                    RTSSCollector._vistos.add(name)

                if basename.lower() in RTSSCollector._EXCLUIDOS:
                    continue

                try:
                    t0, t1, frames = struct.unpack_from("<III", full, base + 0x10C)
                except struct.error:
                    continue
                if t1 > t0 and frames > 0:
                    fps = frames * 1000.0 / (t1 - t0)
                    if best_fps is None or fps > best_fps:
                        best_fps = fps

            return {"fps": round(best_fps)} if best_fps else None
        finally:
            _k32.CloseHandle(h)


class MetricsServer:
    def __init__(self, host="127.0.0.1", port=47200, interval=1.0):
        self.host = host
        self.port = port
        self.interval = interval
        self.gpu = GPUCollector()
        self.cpu = CPUCollector()
        self.rtss = RTSSCollector()
        self._clients: set[web.WebSocketResponse] = set()
        self._overlay_clients: set[web.WebSocketResponse] = set()
        self._runner: web.AppRunner | None = None
        self._broadcast_task: asyncio.Task | None = None
        self.followers: int = 0
        self.subscribers: int = 0
        self._bot_state = None

    async def _overlay_html_handler(self, request: web.Request) -> web.Response:
        return web.Response(text=_OVERLAY_HTML, content_type="text/html", charset="utf-8")

    async def _overlay_ws_handler(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._overlay_clients.add(ws)
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.ERROR:
                    break
        finally:
            self._overlay_clients.discard(ws)
        return ws

    async def push_overlay(self, data: dict) -> None:
        # data debe contener solo str/int/list/dict — json.dumps falla con objetos Python arbitrarios
        if not self._overlay_clients:
            return
        payload = json.dumps(data)
        dead = set()
        for ws in list(self._overlay_clients):
            if ws.closed:
                dead.add(ws)
                continue
            try:
                await ws.send_str(payload)
            except Exception:
                dead.add(ws)
        self._overlay_clients -= dead

    async def _ws_handler(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._clients.add(ws)
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.ERROR:
                    break
        finally:
            self._clients.discard(ws)
        return ws

    def _snapshot(self) -> dict:
        gpu = self.gpu.read() or {}
        cpu = self.cpu.read() or {}
        rtss = self.rtss.read() or {}
        return {
            "ts": time.time(),
            "fps": rtss.get("fps"),
            "gpu_temp": gpu.get("temp_c"),
            "gpu_pct": gpu.get("usage"),
            "vram_pct": gpu.get("vram_pct"),
            "vram_used_mb": gpu.get("vram_used_mb"),
            "vram_total_mb": gpu.get("vram_total_mb"),
            "cpu_pct": cpu.get("usage"),
            "ram_pct": cpu.get("ram_pct"),
            "ram_used_mb": cpu.get("ram_used_mb"),
            "ram_total_mb": cpu.get("ram_total_mb"),
            "followers": self.followers,
            "subscribers": self.subscribers,
            "chat_active": len(self._bot_state.usuarios_activos) if self._bot_state else 0,
            "puntitos": self._bot_state.puntitos_netos_sesion if self._bot_state else 0,
        }

    async def _broadcast_loop(self):
        while True:
            if self._clients:
                payload = json.dumps(self._snapshot())
                dead = set()
                for ws in list(self._clients):
                    if ws.closed:
                        dead.add(ws)
                        continue
                    try:
                        await ws.send_str(payload)
                    except Exception:
                        dead.add(ws)
                self._clients -= dead
            await asyncio.sleep(self.interval)

    async def start(self):
        try:
            _base = sys._MEIPASS
        except AttributeError:
            _base = os.path.abspath(".")
        _images_dir = os.path.join(_base, "storage", "images")

        app = web.Application()
        app.router.add_get("/", self._ws_handler)
        app.router.add_get("/overlay", self._overlay_html_handler)
        app.router.add_get("/ws/overlay", self._overlay_ws_handler)
        if os.path.isdir(_images_dir):
            app.router.add_static("/images", _images_dir)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.host, self.port, reuse_address=True)
        await site.start()
        self._broadcast_task = asyncio.create_task(self._broadcast_loop())
        logger.info(f"[metrics] WebSocket en ws://{self.host}:{self.port}")

    async def stop(self):
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
        if self._runner:
            await self._runner.cleanup()
        logger.info("[metrics] WebSocket cerrado")
