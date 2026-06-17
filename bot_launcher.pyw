import os
import subprocess
import threading
import time
import tkinter as tk
from tkinter import scrolledtext

BOT_DIR = os.path.dirname(os.path.abspath(__file__))
BOT_SCRIPT = os.path.join(BOT_DIR, "bot_del_estadio.py")
AUDIO_MUTED_FLAG          = os.path.join(BOT_DIR, ".audio_muted")
TTS_MUTED_FLAG            = os.path.join(BOT_DIR, ".tts_muted")
METRICS_DISABLED_FLAG     = os.path.join(BOT_DIR, ".metrics_disabled")
EMOJI_OVERLAY_DISABLED_FLAG = os.path.join(BOT_DIR, ".emoji_overlay_disabled")
BOT_PID_FILE          = os.path.join(BOT_DIR, ".bot.pid")
VENV_PYTHON = os.path.join(BOT_DIR, "bot-env", "Scripts", "python.exe")
NO_WINDOW = subprocess.CREATE_NO_WINDOW


def _open_launcher(root: tk.Tk):
    for widget in root.winfo_children():
        widget.destroy()
    root.resizable(True, True)
    root.minsize(700, 500)
    root.geometry("700x500")
    root.deiconify()
    BotLauncher(root)


class UpdateWindow:
    """Shown when a newer commit is available; downloads and applies the update."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Bot del Estadio — Actualizando")
        self.root.resizable(False, False)
        self.root.geometry("460x230")
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self._build_ui()
        self.root.deiconify()
        threading.Thread(target=self._do_update, daemon=True).start()

    def _build_ui(self):
        tk.Label(
            self.root,
            text="Descargando actualizacion...",
            font=("Segoe UI", 12, "bold"),
            pady=12,
        ).pack()
        self.log = scrolledtext.ScrolledText(
            self.root,
            state=tk.DISABLED,
            height=8,
            font=("Consolas", 8),
            bg="#1e1e1e",
            fg="#d4d4d4",
            wrap=tk.WORD,
            padx=6,
            pady=4,
        )
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def _do_update(self):
        import time
        self._log("--- descargando actualizacion ---\n")
        pull = subprocess.run(
            ["git", "pull"],
            cwd=BOT_DIR,
            capture_output=True,
            text=True,
            creationflags=NO_WINDOW,
        )
        self._log(pull.stdout or pull.stderr)

        if pull.returncode == 0:
            self._log("--- instalando dependencias ---\n")
            pip = subprocess.run(
                [VENV_PYTHON, "-m", "pip", "install", "-r",
                 os.path.join(BOT_DIR, "requirements.txt"), "-q"],
                capture_output=True,
                text=True,
                creationflags=NO_WINDOW,
            )
            if pip.stderr:
                self._log(pip.stderr)
            self._log("--- listo, abriendo launcher ---\n")
        else:
            self._log("[!] Error al actualizar. Abriendo launcher de todas formas...\n")

        time.sleep(1.5)
        self.root.after(0, _open_launcher, self.root)

    def _log(self, text: str):
        self.root.after(0, self._append, text)

    def _append(self, text: str):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, text)
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)


class BotLauncher:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Bot del Estadio")
        self.root.minsize(700, 500)
        self.process: subprocess.Popen | None = None
        self.audio_var   = tk.BooleanVar(value=not os.path.exists(AUDIO_MUTED_FLAG))
        self.tts_var     = tk.BooleanVar(value=not os.path.exists(TTS_MUTED_FLAG))
        self.metrics_var = tk.BooleanVar(value=not os.path.exists(METRICS_DISABLED_FLAG))
        self.emoji_var   = tk.BooleanVar(value=not os.path.exists(EMOJI_OVERLAY_DISABLED_FLAG))
        if not self._build_ui():
            return
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        if not os.path.exists(VENV_PYTHON):
            from tkinter import messagebox
            messagebox.showerror(
                "Entorno no encontrado",
                f"No se encontró el entorno virtual en:\n{VENV_PYTHON}\n\n"
                "Re-ejecutá el instalador.",
            )
            self.root.destroy()
            return False

        # ── Header ──────────────────────────────────────────────────────────
        header = tk.Label(
            self.root,
            text="Bot del Estadio",
            font=("Segoe UI", 15, "bold"),
            pady=8,
        )
        header.pack(fill=tk.X)

        tk.Frame(self.root, height=1, bg="#cccccc").pack(fill=tk.X, padx=12)

        # ── Control bar ─────────────────────────────────────────────────────
        bar = tk.Frame(self.root, pady=10)
        bar.pack(fill=tk.X, padx=16)

        self.status_dot = tk.Label(bar, text="●", font=("Segoe UI", 14), fg="#cc3333")
        self.status_dot.pack(side=tk.LEFT)

        self.status_label = tk.Label(
            bar, text=" DETENIDO", font=("Segoe UI", 11), fg="#cc3333"
        )
        self.status_label.pack(side=tk.LEFT, padx=(0, 20))

        self.btn = tk.Button(
            bar,
            text="Iniciar",
            width=10,
            font=("Segoe UI", 10),
            command=self._toggle,
        )
        self.btn.pack(side=tk.LEFT)

        tk.Checkbutton(
            bar,
            text="Audio",
            variable=self.audio_var,
            command=self._toggle_audio,
            font=("Segoe UI", 10),
        ).pack(side=tk.LEFT, padx=(20, 0))

        tk.Checkbutton(
            bar,
            text="Voz",
            variable=self.tts_var,
            command=self._toggle_tts,
            font=("Segoe UI", 10),
        ).pack(side=tk.LEFT, padx=(10, 0))

        tk.Checkbutton(
            bar,
            text="Métricas",
            variable=self.metrics_var,
            command=self._toggle_metrics,
            font=("Segoe UI", 10),
        ).pack(side=tk.LEFT, padx=(10, 0))

        tk.Checkbutton(
            bar,
            text="Emojis",
            variable=self.emoji_var,
            command=self._toggle_emoji_overlay,
            font=("Segoe UI", 10),
        ).pack(side=tk.LEFT, padx=(10, 0))

        # ── Log area ─────────────────────────────────────────────────────────
        self.log = scrolledtext.ScrolledText(
            self.root,
            state=tk.DISABLED,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            wrap=tk.WORD,
            padx=6,
            pady=6,
        )
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        return True

    # ── Bot control ──────────────────────────────────────────────────────────

    def _toggle(self):
        if self.process is None:
            self._start()
        else:
            self._stop()

    def _kill_leftover(self):
        """Mata cualquier proceso bot previo usando el PID guardado en .bot.pid."""
        if not os.path.exists(BOT_PID_FILE):
            return
        try:
            with open(BOT_PID_FILE) as f:
                pid = int(f.read().strip())
            result = subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True,
                creationflags=NO_WINDOW,
            )
            if result.returncode == 0:
                time.sleep(0.5)  # pausa para que el OS libere los puertos
        except (ValueError, OSError):
            pass
        finally:
            try:
                os.remove(BOT_PID_FILE)
            except OSError:
                pass

    def _start(self):
        self._kill_leftover()
        self.process = subprocess.Popen(
            [VENV_PYTHON, "-u", BOT_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=BOT_DIR,
            text=True,
            bufsize=1,
            creationflags=NO_WINDOW,
        )
        try:
            with open(BOT_PID_FILE, "w") as f:
                f.write(str(self.process.pid))
        except OSError:
            pass
        self._set_status(running=True)
        thread = threading.Thread(target=self._read_output, daemon=True)
        thread.start()

    def _stop(self):
        proc = self.process
        if proc is None:
            return
        self.btn.config(state=tk.DISABLED, text="Deteniendo...")
        self._append("--- deteniendo bot ---\n")
        threading.Thread(target=self._kill_tree, args=(proc,), daemon=True).start()

    def _kill_tree(self, proc):
        """Mata el proceso y todos sus hijos (para liberar el pipe de stdout)."""
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                creationflags=NO_WINDOW,
            )
        except OSError:
            try:
                proc.kill()
            except OSError:
                pass

    def _read_output(self):
        proc = self.process
        assert proc and proc.stdout
        for line in iter(proc.stdout.readline, ""):
            self.root.after(0, self._append, line)
        exit_code = proc.wait()
        self.process = None
        self.root.after(0, self._on_process_exit, exit_code)

    def _on_process_exit(self, exit_code: int):
        self._append(f"--- proceso finalizado (código {exit_code}) ---\n")
        try:
            os.remove(BOT_PID_FILE)
        except OSError:
            pass
        self._set_status(running=False)

    # ── UI helpers ───────────────────────────────────────────────────────────

    def _set_status(self, running: bool):
        if running:
            self.status_dot.config(fg="#22aa44")
            self.status_label.config(text=" EN VIVO", fg="#22aa44")
            self.btn.config(text="Detener")
        else:
            self.status_dot.config(fg="#cc3333")
            self.status_label.config(text=" DETENIDO", fg="#cc3333")
            self.btn.config(state=tk.NORMAL, text="Iniciar")

    def _append(self, text: str):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, text)
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def _toggle_audio(self):
        if self.audio_var.get():
            if os.path.exists(AUDIO_MUTED_FLAG):
                os.remove(AUDIO_MUTED_FLAG)
        else:
            open(AUDIO_MUTED_FLAG, "w").close()

    def _toggle_tts(self):
        if self.tts_var.get():
            if os.path.exists(TTS_MUTED_FLAG):
                os.remove(TTS_MUTED_FLAG)
        else:
            open(TTS_MUTED_FLAG, "w").close()

    def _toggle_metrics(self):
        if self.metrics_var.get():
            if os.path.exists(METRICS_DISABLED_FLAG):
                os.remove(METRICS_DISABLED_FLAG)
        else:
            open(METRICS_DISABLED_FLAG, "w").close()

    def _toggle_emoji_overlay(self):
        if self.emoji_var.get():
            if os.path.exists(EMOJI_OVERLAY_DISABLED_FLAG):
                os.remove(EMOJI_OVERLAY_DISABLED_FLAG)
        else:
            open(EMOJI_OVERLAY_DISABLED_FLAG, "w").close()

    def _on_close(self):
        if self.process:
            self.process.terminate()
        try:
            os.remove(BOT_PID_FILE)
        except OSError:
            pass
        self.root.destroy()


if __name__ == "__main__":
    try:
        _branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=BOT_DIR, capture_output=True, text=True,
            creationflags=NO_WINDOW,
        ).stdout.strip()
    except Exception:
        _branch = ""

    root = tk.Tk()

    if _branch != "master":
        BotLauncher(root)
    else:
        root.withdraw()
        root.title("Bot del Estadio")
        root.resizable(False, False)
        root.geometry("300x80")
        tk.Label(
            root,
            text="Verificando actualizaciones...",
            font=("Segoe UI", 11),
            pady=24,
        ).pack()
        root.deiconify()

        def _on_fetch_done(update_needed: bool):
            for widget in root.winfo_children():
                widget.destroy()
            if update_needed:
                UpdateWindow(root)
            else:
                _open_launcher(root)

        def _fetch():
            update_needed = False
            try:
                subprocess.run(
                    ["git", "fetch", "origin", "--quiet"],
                    cwd=BOT_DIR, capture_output=True, timeout=15,
                    creationflags=NO_WINDOW,
                )
                behind = subprocess.run(
                    ["git", "rev-list", "--count", "HEAD..@{u}"],
                    cwd=BOT_DIR, capture_output=True, text=True,
                    creationflags=NO_WINDOW,
                ).stdout.strip()
                update_needed = behind.isdigit() and int(behind) > 0
            except Exception:
                pass
            root.after(0, _on_fetch_done, update_needed)

        threading.Thread(target=_fetch, daemon=True).start()

    root.mainloop()
