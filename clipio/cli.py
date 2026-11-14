"""The `clipio` command: starts the app, opens the panel and manages items from a terminal."""
import json
import subprocess
import sys
import time

from . import __version__

USAGE = """usage: clipio <command>

  run               run the Clipio service in this terminal (stops with Ctrl+C)
  start             start Clipio in the background
  stop              quit the running Clipio
  toggle|show|hide  open or close the panel
  next              paste the next item of the paste queue (bind it to a key)
  paste <id>        paste an item into the active window
  copy <id>         put an item on the clipboard
  pin <id>          pin or unpin an item
  delete <id>       delete an item
  clear             delete every unpinned item
  pause|resume      pause or resume recording
  purge             apply the retention rules now
  retention <days>  keep items for 1-365 days and clean up now
  autostart on|off  start Clipio at login (or stop doing so)
  list              print the stored items
  status            print a short status summary
  version           print the version
  setup [--silent]  install or update the packaged app (opens the setup window)
  uninstall [--silent]  remove the packaged app (history and settings stay)
"""

UI_COMMANDS = {"toggle", "show", "hide", "next"}
ID_COMMANDS = {"pin", "delete"}


# Start `python -m clipio run` detached from this terminal
def spawn_background() -> None:
    from .system.autostart import command
    kwargs = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if sys.platform == "win32":
        kwargs["creationflags"] = 0x00000008 | 0x00000200   # DETACHED_PROCESS | NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(command(), **kwargs)


# Make sure the app is running; start it and wait up to `wait` seconds if needed
def ensure_running(wait: float = 10.0) -> bool:
    from . import ipc
    if ipc.is_running():
        return True
    spawn_background()
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        time.sleep(0.2)
        if ipc.is_running():
            return True
    return False


# Tell a running app to reload its state (no-op when it is not running)
def notify_refresh() -> None:
    from . import ipc
    ipc.send("refresh", 500)


# Print the stored items as JSON lines
def list_items(con) -> None:
    from .core import db
    for r in db.list_items(con):
        text = (r["text"] or r["image_file"] or "").replace("\n", " ")[:80]
        print(json.dumps({"id": r["id"], "kind": r["kind"], "pinned": bool(r["pinned"]), "text": text},
                         ensure_ascii=False))


# Print a short status summary as JSON
def status(con) -> None:
    from . import ipc
    from .core import config, paths
    print(json.dumps({
        "running": ipc.is_running(),
        "panel_loaded": ipc.is_running(ipc.PANEL),
        "items": con.execute("SELECT COUNT(*) FROM items").fetchone()[0],
        "paused": paths.pause_file().exists(),
        "retention_days": config.load()["retention_days"],
        "db": str(paths.db_file()),
    }))


# Run a command that only needs the database
def db_command(cmd: str, args: list[str]) -> int:
    from .core import actions, db, maintenance
    con = db.connect()
    if cmd in ID_COMMANDS:
        if not args or not args[0].isdigit():
            print(f"usage: clipio {cmd} <id>", file=sys.stderr)
            return 2
        (actions.toggle_pin if cmd == "pin" else actions.delete)(con, int(args[0]))
    elif cmd == "clear":
        print(f"deleted {actions.clear(con)} items")
    elif cmd in ("pause", "resume"):
        actions.set_paused(cmd == "pause")
    elif cmd == "purge":
        maintenance.run(con)
    elif cmd == "retention":
        if not args or not args[0].isdigit():
            print("usage: clipio retention <days>", file=sys.stderr)
            return 2
        print(f"keeping items for {actions.set_retention(con, int(args[0]))} days")
    elif cmd == "list":
        list_items(con)
        return 0
    elif cmd == "status":
        status(con)
        return 0
    else:
        print(USAGE, file=sys.stderr)
        return 2
    notify_refresh()
    return 0


# Turn starting at login on or off
def autostart_command(args: list[str]) -> int:
    from .system import autostart
    if args[:1] == ["on"]:
        autostart.set_enabled(True)
    elif args[:1] == ["off"]:
        autostart.set_enabled(False)
    elif args:
        print("usage: clipio autostart on|off", file=sys.stderr)
        return 2
    print("autostart is", "on" if autostart.is_enabled() else "off")
    return 0


# Send a command to the running app, starting it first when needed
def app_command(command: str) -> int:
    from . import ipc
    if not ensure_running():
        print("clipio: could not start Clipio (is PySide6 installed?)", file=sys.stderr)
        return 1
    return 0 if ipc.send(command) == "ok" else 1


# Install or remove the packaged app, with the setup window or silently
def setup_command(cmd: str, args: list[str]) -> int:
    from .setup import window
    remove = cmd == "uninstall"
    return window.run_silent(remove) if "--silent" in args else window.run_setup(remove)


# Packaged app started without arguments (double click): set up, or open the panel
def launch_packaged() -> int:
    from .setup import install
    if not install.running_installed():
        return setup_command("setup", [])
    return app_command("show")


# Entry point of the `clipio` command
def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    argv = [a for a in argv if not a.startswith("-psn_")]   # old macOS adds a process serial number
    if not argv and getattr(sys, "frozen", False):
        return launch_packaged()
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    cmd, args = argv[0], argv[1:]
    if cmd in ("version", "--version"):
        print(__version__)
        return 0
    if cmd == "run":
        from .app import run
        return run([sys.argv[0]])
    if cmd == "panel":   # started by the service when the panel opens
        from .panel import run as run_panel
        return run_panel([sys.argv[0]])
    if cmd == "start":
        return 0 if ensure_running() else 1
    if cmd == "stop":
        from . import ipc
        ipc.send("quit", 1000)
        return 0
    if cmd in UI_COMMANDS:
        return app_command(cmd)
    if cmd in ("paste", "copy"):
        if not args or not args[0].isdigit():
            print(f"usage: clipio {cmd} <id>", file=sys.stderr)
            return 2
        return app_command(f"{cmd} {args[0]}")
    if cmd == "autostart":
        return autostart_command(args)
    if cmd in ("setup", "uninstall"):
        return setup_command(cmd, args)
    return db_command(cmd, args)


# Entry point of the windowed `clipio-gui` launcher (no console on Windows)
def gui_main() -> int:
    from .app import run
    return run(sys.argv[:1])


if __name__ == "__main__":
    sys.exit(main())
