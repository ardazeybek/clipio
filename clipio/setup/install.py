"""Installs, updates and removes the packaged Clipio app for the current user (no admin rights needed).

The packaged builds (see `packaging/`) carry the whole app:
- Windows and Linux: a single setup file; the app's files are unpacked into `sys._MEIPASS` and the
  small onedir launcher sits in `payload/`. Installing copies both into the install folder.
- macOS: `Clipio.app` (in a disk image); installing copies the bundle into Applications.
User data (history, settings) lives elsewhere and is never touched.
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .. import __version__
from ..system import autostart

NAME = "Clipio"
EXE = "Clipio.exe" if sys.platform == "win32" else ("Clipio" if sys.platform == "darwin" else "clipio")
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Clipio"
LINUX_HELPERS = {   # tool -> package name (same on apt, dnf, pacman, zypper)
    "wl-copy": "wl-clipboard", "wl-paste": "wl-clipboard", "xdotool": "xdotool", "wtype": "wtype",
}


# ---- locations ----

# Folder (or .app bundle on macOS) the app is installed into
def target_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "Programs" / NAME
    if sys.platform == "darwin":
        system_apps = Path("/Applications")
        apps = system_apps if os.access(system_apps, os.W_OK) else Path.home() / "Applications"
        return apps / f"{NAME}.app"
    return Path.home() / ".local" / "lib" / "clipio"


# The installed executable
def target_exe() -> Path:
    if sys.platform == "darwin":
        return target_dir() / "Contents" / "MacOS" / EXE
    return target_dir() / EXE


# True when this process is the installed copy (not the setup file or the disk image)
def running_installed() -> bool:
    try:
        Path(sys.executable).resolve().relative_to(target_dir().resolve())
        return True
    except (ValueError, OSError):
        return False


# Version of the installed app ('' when not installed)
def installed_version() -> str:
    f = target_dir() / ("Contents/Resources/version.txt" if sys.platform == "darwin" else "version.txt")
    try:
        return f.read_text(encoding="utf-8").strip()
    except OSError:
        return "?" if target_exe().exists() else ""


# ---- steps (each returns None or raises) ----

# Ask a running Clipio (service and panel) to quit so its files can be replaced
def stop_running() -> None:
    from .. import ipc
    for channel in (ipc.PANEL, ""):   # panel first, then the service
        ipc.send("quit", 800, channel)
    for _ in range(30):
        if not ipc.is_running():
            break
        time.sleep(0.1)
    time.sleep(0.3)   # Windows: let the processes release their files


# Copy the app into its install folder (fresh copy next to it, then swapped in)
def copy_files() -> None:
    dest = target_dir()
    dest.parent.mkdir(parents=True, exist_ok=True)
    fresh = dest.with_name(dest.name + ".new")
    old = dest.with_name(dest.name + ".old")
    for d in (fresh, old):
        shutil.rmtree(d, ignore_errors=True)
    if sys.platform == "darwin":
        shutil.copytree(Path(sys.executable).parents[2], fresh, symlinks=True)
        (fresh / "Contents/Resources/version.txt").write_text(__version__, encoding="utf-8")
    else:
        bundle = Path(getattr(sys, "_MEIPASS", ""))
        shutil.copytree(bundle, fresh / "_internal", ignore=shutil.ignore_patterns("payload"))
        shutil.copy2(bundle / "payload" / EXE, fresh / EXE)
        (fresh / "version.txt").write_text(__version__, encoding="utf-8")
    if dest.exists():
        dest.rename(old)
    fresh.rename(dest)
    shutil.rmtree(old, ignore_errors=True)


# Start menu / app launcher entry, plus the uninstall entry on Windows and `clipio` on the Linux PATH
def add_shortcuts() -> None:
    exe = str(target_exe())
    if sys.platform == "win32":
        _windows_shortcut(exe)
        _windows_uninstall_entry(exe)
    elif sys.platform == "darwin":
        subprocess.run(["xattr", "-dr", "com.apple.quarantine", str(target_dir())], capture_output=True)
    else:
        _linux_entries(exe)


# Start Clipio when the user logs in
def enable_autostart() -> None:
    autostart.set_enabled(True, str(target_exe()))


# Linux tools Clipio needs for this desktop that are missing
def missing_helpers() -> list[str]:
    if not sys.platform.startswith("linux"):
        return []
    wayland = os.environ.get("XDG_SESSION_TYPE") == "wayland" or "WAYLAND_DISPLAY" in os.environ
    need = ["wl-copy", "wl-paste"] if wayland else ["xdotool"]
    if wayland and "HYPRLAND_INSTANCE_SIGNATURE" not in os.environ:
        need.append("wtype")
    return sorted({LINUX_HELPERS[t] for t in need if not shutil.which(t)})


# Install missing Linux helpers with the system package manager (asks for the password graphically)
def install_helpers() -> list[str]:
    pkgs = missing_helpers()
    if not pkgs:
        return []
    managers = {"apt-get": ["apt-get", "install", "-y"], "dnf": ["dnf", "install", "-y"],
                "pacman": ["pacman", "-S", "--needed", "--noconfirm"], "zypper": ["zypper", "--non-interactive", "install"]}
    pm = next((m for m in managers if shutil.which(m)), None)
    if pm and shutil.which("pkexec"):
        subprocess.run(["pkexec", *managers[pm], *pkgs], capture_output=True, timeout=600)
    return missing_helpers()   # what is still missing (shown on the last page)


# Start the installed app in the background and wait until it answers
def launch() -> bool:
    from .. import ipc
    kwargs: dict = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if sys.platform == "win32":
        kwargs["creationflags"] = 0x00000008 | 0x00000200   # DETACHED_PROCESS | NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    env = {k: v for k, v in os.environ.items() if not k.startswith(("_MEI", "_PYI"))}
    subprocess.Popen(autostart.command(str(target_exe())), env=env, **kwargs)
    for _ in range(100):
        if ipc.is_running():
            return True
        time.sleep(0.1)
    return False


# ---- removal ----

# Remove the app, its shortcuts and autostart entry (history and settings stay)
def uninstall() -> None:
    stop_running()
    autostart.set_enabled(False)
    if sys.platform == "win32":
        _windows_remove_entries()
    elif sys.platform.startswith("linux"):
        _linux_remove_entries()
    dest = target_dir()
    if sys.platform == "win32" and running_installed():
        # a running exe cannot delete its own folder: let cmd do it once this process ended
        subprocess.Popen(f'cmd /c ping -n 3 127.0.0.1 >nul & rmdir /s /q "{dest}"',
                         creationflags=0x08000000, close_fds=True)   # CREATE_NO_WINDOW
    else:
        shutil.rmtree(dest, ignore_errors=True)


# ---- Windows details ----

# Start menu shortcut through the Windows Script Host (no extra packages)
def _windows_shortcut(exe: str) -> None:
    lnk = Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/Clipio.lnk"
    ps = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}');"
          f"$s.TargetPath='{exe}';$s.WorkingDirectory='{Path(exe).parent}';$s.IconLocation='{exe},0';$s.Save()")
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                   capture_output=True, creationflags=0x08000000, timeout=60)


# "Apps & features" entry so Clipio can be removed like any other app
def _windows_uninstall_entry(exe: str) -> None:
    import winreg
    size_kb = sum(f.stat().st_size for f in target_dir().rglob("*") if f.is_file()) // 1024
    values = {"DisplayName": NAME, "DisplayVersion": __version__, "Publisher": "Arda Zeybek",
              "DisplayIcon": exe, "InstallLocation": str(target_dir()),
              "UninstallString": f'"{exe}" uninstall', "QuietUninstallString": f'"{exe}" uninstall --silent',
              "URLInfoAbout": "https://github.com/ardazeybek/clipio"}
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY, 0, winreg.KEY_SET_VALUE) as key:
        for k, v in values.items():
            winreg.SetValueEx(key, k, 0, winreg.REG_SZ, v)
        for k, v in {"NoModify": 1, "NoRepair": 1, "EstimatedSize": size_kb}.items():
            winreg.SetValueEx(key, k, 0, winreg.REG_DWORD, v)


# Remove the shortcut and the uninstall entry
def _windows_remove_entries() -> None:
    import winreg
    (Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/Clipio.lnk").unlink(missing_ok=True)
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
    except OSError:
        pass


# ---- Linux details ----

# Launcher entry, icon and a `clipio` command in ~/.local/bin
def _linux_paths() -> tuple[Path, Path, Path]:
    share = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return (share / "applications" / "clipio.desktop",
            share / "icons" / "hicolor" / "scalable" / "apps" / "clipio.svg",
            Path.home() / ".local" / "bin" / "clipio")


# Write the launcher entry, icon and command link
def _linux_entries(exe: str) -> None:
    desktop, icon, link = _linux_paths()
    for p in (desktop, icon, link):
        p.parent.mkdir(parents=True, exist_ok=True)
    svg = target_dir() / "_internal" / "clipio" / "ui" / "assets" / "clipio.svg"
    if svg.exists():
        shutil.copy2(svg, icon)
    desktop.write_text("[Desktop Entry]\nType=Application\nName=Clipio\nGenericName=Clipboard history\n"
                       f"Comment=A paper-themed clipboard history\nExec=\"{exe}\"\nIcon=clipio\n"
                       "Terminal=false\nCategories=Utility;\nKeywords=clipboard;paste;history;\n"
                       "StartupWMClass=clipio\n", encoding="utf-8")
    if link.is_symlink() or not link.exists():   # never replace a user's own `clipio` script
        link.unlink(missing_ok=True)
        link.symlink_to(exe)


# Remove the launcher entry, icon and command link
def _linux_remove_entries() -> None:
    desktop, icon, link = _linux_paths()
    desktop.unlink(missing_ok=True)
    icon.unlink(missing_ok=True)
    if link.is_symlink():
        link.unlink()
