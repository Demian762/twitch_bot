"""
Diagnóstico del flujo de métricas en dos modos:

  1. Modo colectores (sin bot corriendo):
       python test_metrics.py

  2. Modo WebSocket (con bot corriendo):
       python test_metrics.py ws
"""

import ctypes
import sys
import time


def _rtss_status() -> str:
    """Devuelve el estado actual de RTSS en texto para diagnóstico."""
    import ctypes.wintypes
    k32 = ctypes.windll.kernel32
    k32.OpenFileMappingW.restype = ctypes.wintypes.HANDLE
    k32.OpenFileMappingW.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.LPCWSTR]
    k32.CloseHandle.restype = ctypes.wintypes.BOOL
    k32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]

    h = k32.OpenFileMappingW(0x0004, False, "RTSSSharedMemoryV2")
    if not h:
        return "NO CORRE (shared memory no existe — abrí RTSS)"
    k32.CloseHandle(h)
    return "CORRE (shared memory OK, pero sin juego activo aún)"


def test_collectors():
    """Lee directamente GPU, CPU y RTSS sin WebSocket."""
    from utils.metrics_server import GPUCollector, CPUCollector, RTSSCollector

    gpu  = GPUCollector()
    cpu  = CPUCollector()
    rtss = RTSSCollector()

    print(f"Estado RTSS: {_rtss_status()}\n")
    print("Leyendo métricas cada 1s (Ctrl+C para salir)\n")
    try:
        while True:
            g = gpu.read()
            c = cpu.read()
            r = rtss.read()

            fps_val  = r.get("fps")      if r else None
            gpu_temp = g.get("temp_c")   if g else None
            gpu_pct  = g.get("usage")    if g else None
            vram_pct = g.get("vram_pct") if g else None
            cpu_pct  = c.get("usage")    if c else None
            ram_pct  = c.get("ram_pct")  if c else None

            fps_str = str(fps_val) if fps_val is not None else "NULL"

            print(
                f"FPS={fps_str:>6}  "
                f"GPU={gpu_pct}%/{gpu_temp}°C  "
                f"VRAM={vram_pct}%  "
                f"CPU={cpu_pct}%  "
                f"RAM={ram_pct}%"
            )
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nListo.")


def test_websocket():
    """Se conecta al WebSocket del bot y muestra los mensajes recibidos."""
    import asyncio
    import json
    import aiohttp

    async def run():
        uri = "ws://127.0.0.1:47200"
        print(f"Conectando a {uri}  (Ctrl+C para salir)\n")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(uri) as ws:
                    print("Conexión OK. Esperando mensajes...\n")
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            fps_val = data.get("fps")
                            fps_str = str(fps_val) if fps_val is not None else "NULL"
                            print(
                                f"FPS={fps_str:>6}  "
                                f"GPU={data.get('gpu_pct')}%/{data.get('gpu_temp')}°C  "
                                f"VRAM={data.get('vram_pct')}%  "
                                f"CPU={data.get('cpu_pct')}%  "
                                f"RAM={data.get('ram_pct')}%"
                            )
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"ERROR WebSocket: {ws.exception()}")
                            break
        except aiohttp.ClientConnectorError:
            print("ERROR: no hay nadie escuchando en ws://127.0.0.1:47200")
            print("Asegurate de que el bot esté corriendo antes de usar el modo 'ws'.")
        except KeyboardInterrupt:
            print("\nListo.")

    asyncio.run(run())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "ws":
        test_websocket()
    else:
        test_collectors()
