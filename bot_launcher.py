import os
import subprocess
import threading
import tkinter as tk
from tkinter import scrolledtext

BOT_DIR = os.path.dirname(os.path.abspath(__file__))
BOT_SCRIPT = os.path.join(BOT_DIR, "bot_del_estadio.py")
AUDIO_MUTED_FLAG = os.path.join(BOT_DIR, ".audio_muted")
VENV_PYTHON = os.path.join(BOT_DIR, "bot-env", "Scripts", "python.exe")
NO_WINDOW = subprocess.CREATE_NO_WINDOW


class BotLauncher:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Bot del Estadio")
        self.root.minsize(700, 500)
        self.process: subprocess.Popen | None = None
        self.audio_var = tk.BooleanVar(value=not os.path.exists(AUDIO_MUTED_FLAG))
        if not self._build_ui():
            return
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        threading.Thread(target=self._check_updates, daemon=True).start()

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

    # ── Update check ─────────────────────────────────────────────────────────

    def _check_updates(self):
        try:
            subprocess.run(
                ["git", "fetch", "origin", "--quiet"],
                cwd=BOT_DIR, capture_output=True, timeout=15,
                creationflags=NO_WINDOW,
            )
            local = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=BOT_DIR, capture_output=True, text=True,
                creationflags=NO_WINDOW,
            ).stdout.strip()
            remote = subprocess.run(
                ["git", "rev-parse", "@{u}"],
                cwd=BOT_DIR, capture_output=True, text=True,
                creationflags=NO_WINDOW,
            ).stdout.strip()
            if local and remote and local != remote:
                self._run_update()
        except Exception:
            pass

    def _run_update(self):
        def log(text):
            self.root.after(0, self._append, text)

        log("--- actualizando bot ---\n")
        pull = subprocess.run(
            ["git", "pull"], cwd=BOT_DIR, capture_output=True, text=True,
            creationflags=NO_WINDOW,
        )
        log(pull.stdout or pull.stderr)
        if pull.returncode == 0:
            log("--- instalando dependencias ---\n")
            pip = subprocess.run(
                [VENV_PYTHON, "-m", "pip", "install", "-r",
                 os.path.join(BOT_DIR, "requirements.txt"), "-q"],
                capture_output=True, text=True,
                creationflags=NO_WINDOW,
            )
            if pip.stderr:
                log(pip.stderr)
            log("--- actualización completa ---\n")
        else:
            log("[!] Error al actualizar.\n")

    # ── Bot control ──────────────────────────────────────────────────────────

    def _toggle(self):
        if self.process is None:
            self._start()
        else:
            self._stop()

    def _start(self):
        self.process = subprocess.Popen(
            [VENV_PYTHON, "-u", BOT_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=BOT_DIR,
            text=True,
            bufsize=1,
            creationflags=NO_WINDOW,
        )
        self._set_status(running=True)
        thread = threading.Thread(target=self._read_output, daemon=True)
        thread.start()

    def _stop(self):
        proc = self.process
        if proc is None:
            return
        self.btn.config(state=tk.DISABLED, text="Deteniendo...")
        self._append("--- deteniendo bot ---\n")
        try:
            proc.terminate()
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

    def _on_close(self):
        if self.process:
            self.process.terminate()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    BotLauncher(root)
    root.mainloop()
