import os
import sys
import shutil
import subprocess
import threading
import winreg
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from pathlib import Path

REPO_URL = "https://github.com/Demian762/twitch_bot.git"
VENV_NAME = "bot-env"


def _refresh_path_from_registry():
    """Reload PATH from registry so freshly installed tools are found."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            user_path = winreg.QueryValueEx(key, "PATH")[0]
    except Exception:
        user_path = ""
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ) as key:
            sys_path = winreg.QueryValueEx(key, "Path")[0]
    except Exception:
        sys_path = ""
    os.environ["PATH"] = sys_path + ";" + user_path


def _find_python() -> str | None:
    """Find python.exe after a fresh install (common locations)."""
    local = Path(os.environ.get("LOCALAPPDATA", ""))
    candidates = sorted(
        (local / "Programs" / "Python").glob("Python3*/python.exe"), reverse=True
    )
    for p in candidates:
        if p.exists():
            return str(p)
    for p in Path("C:/").glob("Python3*/python.exe"):
        return str(p)
    return None


class Installer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Bot del Estadio — Instalador")
        self.root.minsize(640, 480)
        self.secretos_path: str | None = None
        self._build_ui()

    def _build_ui(self):
        tk.Label(
            self.root,
            text="Instalador — Bot del Estadio",
            font=("Segoe UI", 14, "bold"),
            pady=10,
        ).pack(fill=tk.X)

        tk.Frame(self.root, height=1, bg="#cccccc").pack(fill=tk.X, padx=12)

        form = tk.Frame(self.root, pady=10)
        form.pack(fill=tk.X, padx=16)

        # Folder row
        tk.Label(form, text="Carpeta de instalación:", font=("Segoe UI", 10), width=22, anchor="w").grid(
            row=0, column=0, sticky="w", pady=4
        )
        self.folder_var = tk.StringVar(value=str(Path.home() / "BotDelEstadio"))
        tk.Entry(form, textvariable=self.folder_var, font=("Segoe UI", 9), width=38).grid(
            row=0, column=1, padx=(0, 6)
        )
        tk.Button(form, text="...", font=("Segoe UI", 9), command=self._choose_folder).grid(row=0, column=2)

        # Secretos row
        tk.Label(form, text="Archivo secretos.py:", font=("Segoe UI", 10), width=22, anchor="w").grid(
            row=1, column=0, sticky="w", pady=4
        )
        self.secretos_var = tk.StringVar(value="(no seleccionado)")
        tk.Label(form, textvariable=self.secretos_var, font=("Segoe UI", 9), fg="#555", anchor="w").grid(
            row=1, column=1, sticky="w", padx=(0, 6)
        )
        tk.Button(form, text="Seleccionar", font=("Segoe UI", 9), command=self._choose_secretos).grid(
            row=1, column=2
        )

        # Install button
        btn_bar = tk.Frame(self.root, pady=6)
        btn_bar.pack(fill=tk.X, padx=16)
        self.install_btn = tk.Button(
            btn_bar,
            text="Instalar",
            width=14,
            font=("Segoe UI", 10, "bold"),
            command=self._start_install,
            bg="#0078d4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
        )
        self.install_btn.pack(side=tk.LEFT)

        # Log
        self.log = scrolledtext.ScrolledText(
            self.root,
            state=tk.DISABLED,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            wrap=tk.WORD,
            padx=6,
            pady=6,
        )
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # ── Picker callbacks ──────────────────────────────────────────────────────

    def _choose_folder(self):
        path = filedialog.askdirectory(title="Elegir carpeta de instalación")
        if path:
            self.folder_var.set(path)

    def _choose_secretos(self):
        path = filedialog.askopenfilename(
            title="Seleccionar secretos.py",
            filetypes=[("Python files", "*.py"), ("Todos los archivos", "*.*")],
        )
        if path:
            self.secretos_path = path
            self.secretos_var.set(Path(path).name)

    # ── Install flow ──────────────────────────────────────────────────────────

    def _start_install(self):
        if not self.secretos_path:
            messagebox.showwarning("Falta secretos.py", "Seleccioná el archivo secretos.py antes de instalar.")
            return
        install_dir = Path(self.folder_var.get().strip())
        if install_dir.exists() and any(install_dir.iterdir()):
            messagebox.showwarning(
                "Carpeta no vacía",
                f"La carpeta ya existe y no está vacía:\n{install_dir}\n\n"
                "Elegí una carpeta vacía o una carpeta nueva para continuar.",
            )
            return
        self.install_btn.config(state=tk.DISABLED, text="Instalando...")
        threading.Thread(target=self._install, args=(install_dir,), daemon=True).start()

    def _install(self, install_dir: Path):
        try:
            python_exe = self._ensure_python()
            if python_exe is None:
                return
            if not self._ensure_git():
                return
            if not self._clone(install_dir):
                return
            if not self._create_venv(install_dir, python_exe):
                return
            if not self._pip_install(install_dir):
                return
            self._copy_secretos(install_dir)
            self._create_shortcut(install_dir)
            self._log("\n✓ ¡Instalación completa!")
            self.root.after(
                0,
                messagebox.showinfo,
                "¡Listo!",
                "Bot del Estadio instalado correctamente.\nUsá el acceso directo del escritorio para abrirlo.",
            )
        except Exception as e:
            self._log(f"\n[!] Error inesperado: {e}")
        finally:
            self.root.after(0, lambda: self.install_btn.config(state=tk.NORMAL, text="Instalar"))

    def _ensure_python(self) -> str | None:
        self._log("→ Verificando Python...")
        result = subprocess.run("python --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            self._log(f"  {result.stdout.strip() or result.stderr.strip()} — OK")
            return "python"
        self._log("  No encontrado. Instalando via winget (puede tardar)...")
        ok = self._run("winget install Python.Python.3 --silent --accept-package-agreements --accept-source-agreements")
        if not ok:
            self._log("[!] No se pudo instalar Python automáticamente.")
            self._log("    Instalalo manualmente desde python.org y volvé a intentar.")
            return None
        _refresh_path_from_registry()
        # Try shell path first, then known locations
        result = subprocess.run("python --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return "python"
        found = _find_python()
        if found:
            self._log(f"  Python encontrado en: {found}")
            return found
        self._log("[!] Python instalado pero no encontrado. Reiniciá el instalador.")
        return None

    def _ensure_git(self) -> bool:
        self._log("→ Verificando Git...")
        result = subprocess.run("git --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            self._log(f"  {result.stdout.strip()} — OK")
            return True
        self._log("  No encontrado. Instalando via winget (puede tardar)...")
        ok = self._run(
            "winget install Git.Git --silent --accept-package-agreements --accept-source-agreements"
        )
        if not ok:
            self._log("[!] No se pudo instalar Git automáticamente.")
            self._log("    Instalalo manualmente desde git-scm.com y volvé a intentar.")
            return False
        _refresh_path_from_registry()
        result = subprocess.run("git --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            self._log(f"  {result.stdout.strip()} — OK")
            return True
        self._log("[!] Git instalado pero no encontrado. Reiniciá el instalador.")
        return False

    def _clone(self, install_dir: Path) -> bool:
        self._log(f"→ Clonando repositorio en {install_dir}...")
        install_dir.parent.mkdir(parents=True, exist_ok=True)
        return self._run(f'git clone "{REPO_URL}" "{install_dir}"')

    def _create_venv(self, install_dir: Path, python_exe: str) -> bool:
        self._log("→ Creando entorno virtual...")
        venv_path = install_dir / VENV_NAME
        return self._run(f'"{python_exe}" -m venv "{venv_path}"')

    def _pip_install(self, install_dir: Path) -> bool:
        self._log("→ Instalando dependencias (puede tardar unos minutos)...")
        pip = install_dir / VENV_NAME / "Scripts" / "pip.exe"
        req = install_dir / "requirements.txt"
        return self._run(f'"{pip}" install -r "{req}"')

    def _copy_secretos(self, install_dir: Path):
        self._log("→ Copiando secretos.py...")
        dest = install_dir / "utils" / "secretos.py"
        shutil.copy(self.secretos_path, dest)  # type: ignore[arg-type]

    def _create_shortcut(self, install_dir: Path):
        self._log("→ Creando acceso directo en el escritorio...")
        python_exe = install_dir / VENV_NAME / "Scripts" / "pythonw.exe"
        launcher = install_dir / "bot_launcher.py"
        ps = (
            "$desktop = [System.Environment]::GetFolderPath('Desktop');"
            "$shortcut = Join-Path $desktop 'Bot del Estadio.lnk';"
            f"$s = (New-Object -COM WScript.Shell).CreateShortcut($shortcut);"
            f"$s.TargetPath = '{python_exe}';"
            f"$s.Arguments = '\"{launcher}\"';"
            f"$s.WorkingDirectory = '{install_dir}';"
            "$s.Save()"
        )
        result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
        if result.returncode != 0:
            self._log(f"[!] No se pudo crear el acceso directo: {result.stderr.strip()}")
        else:
            self._log("  Acceso directo creado OK")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _run(self, cmd: str) -> bool:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.stdout:
                self._log(result.stdout.strip())
            if result.returncode != 0 and result.stderr:
                self._log(f"[!] {result.stderr.strip()}")
            return result.returncode == 0
        except Exception as e:
            self._log(f"[!] {e}")
            return False

    def _log(self, text: str):
        self.root.after(0, self._append, text + "\n")

    def _append(self, text: str):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, text)
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    Installer(root)
    root.mainloop()
