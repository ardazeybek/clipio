"""Service side of the panel: starts the panel process when needed and sends it commands.

The panel (QML, graphics driver, fonts) needs most of Clipio's memory, so it runs in its own
process that the service starts on demand and that quits by itself after a while unused.
The service never waits for the panel, so the two can never block each other.
"""
import subprocess
import sys
import time

from . import ipc
from .system import autostart

START_TIMEOUT = 15.0   # seconds to wait for a starting panel before trying again


class PanelLink:
    """Tracks whether the panel process runs and is open; shows, hides and refreshes it."""

    def __init__(self, before_show=None):
        self.shown = False            # the panel reported that it is open
        self.running = False          # a panel process answered recently
        self._proc = None
        self._starting_since = 0.0
        self._before_show = before_show or (lambda: None)

    # ---- commands ----

    # Open the panel: tell the running one, or start a new process that opens itself
    def show(self) -> None:
        self._reap()
        if self._starting():
            return
        self._before_show()
        if sys.platform == "win32":
            from .system import windows
            windows.allow_foreground()
        if self.running:
            ipc.post("show", ipc.PANEL, on_fail=self._spawn)
        else:
            self._spawn()

    # Close the panel
    def hide(self) -> None:
        if self.running:
            ipc.post("hide", ipc.PANEL, on_fail=self._lost)

    # Open or close the panel
    def toggle(self) -> None:
        self.hide() if self.shown and self.running else self.show()

    # Ask an open panel to reload its items
    def refresh(self) -> None:
        if self.running:
            ipc.post("refresh", ipc.PANEL, on_fail=self._lost)

    # Ask the panel process to quit
    def quit(self) -> None:
        if self.running:
            ipc.send("quit", 500, ipc.PANEL)

    # ---- reports from the panel ----

    # Handle "panel <state>" from the panel process (ready, shown, hidden, exit)
    def report(self, state: str) -> str:
        if state in ("ready", "shown", "hidden"):
            self.running = True
            self._starting_since = 0.0
            self.shown = state == "shown" or (state == "ready" and self.shown)
        elif state == "exit":
            self._lost()
        else:
            return "unknown command"
        return "ok"

    # ---- process ----

    # Start the panel process; it opens itself and reports back
    def _spawn(self) -> None:
        self.running = False
        self._starting_since = time.monotonic()
        kwargs = {"stdin": subprocess.DEVNULL}
        if sys.platform == "win32":
            kwargs["creationflags"] = 0x08000000   # CREATE_NO_WINDOW
        try:
            self._proc = subprocess.Popen(autostart.panel_command(), **kwargs)
        except OSError as e:
            print(f"clipio: could not start the panel: {e}", file=sys.stderr)
            self._starting_since = 0.0

    # True while a started panel has not reported back yet
    def _starting(self) -> bool:
        if not self._starting_since:
            return False
        if self._proc is not None and self._proc.poll() is not None:   # it died while starting
            self._starting_since = 0.0
            return False
        return time.monotonic() - self._starting_since < START_TIMEOUT

    # The panel is gone (quit, crashed or never answered)
    def _lost(self) -> None:
        self.running = False
        self.shown = False
        self._reap()

    # Collect a finished panel process so it does not linger as a zombie
    def _reap(self) -> None:
        if self._proc is not None and self._proc.poll() is not None:
            self._proc = None
