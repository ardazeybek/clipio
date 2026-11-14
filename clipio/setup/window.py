"""The setup window: a small paper-themed QML wizard that installs, updates or removes Clipio.

`run_setup()` is what the packaged setup file shows; `--silent` installs without a window
(used by stores and scripts). Work runs on a thread so the animations stay smooth.
"""
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

from .. import __version__
from . import install

UI = Path(__file__).resolve().parent.parent / "ui" / "Setup.qml"
MIN_STEP_S = 0.45   # each step stays on screen at least this long, so the progress reads well

INSTALL_STEPS = [
    ("Closing Clipio", install.stop_running),
    ("Copying files", install.copy_files),
    ("Adding shortcuts", install.add_shortcuts),
    ("Starting with your computer", install.enable_autostart),
]
UNINSTALL_STEPS = [("Removing Clipio", install.uninstall)]


class SetupController(QObject):
    """State of the wizard for QML: mode, progress, current step and the result."""

    changed = Signal()

    # Read what is installed now to pick the mode (install, update, uninstall)
    def __init__(self, uninstall: bool = False):
        super().__init__()
        self._old = install.installed_version()
        self._mode = "uninstall" if uninstall else ("update" if self._old else "install")
        self._step, self._progress, self._state, self._error = "", 0.0, "ready", ""
        self._missing: list[str] = []

    mode = Property(str, lambda s: s._mode, notify=changed)
    version = Property(str, lambda s: __version__, constant=True)
    oldVersion = Property(str, lambda s: s._old, notify=changed)
    step = Property(str, lambda s: s._step, notify=changed)
    progress = Property(float, lambda s: s._progress, notify=changed)
    state = Property(str, lambda s: s._state, notify=changed)   # ready | working | done | failed
    error = Property(str, lambda s: s._error, notify=changed)
    missing = Property("QVariantList", lambda s: s._missing, notify=changed)
    platform = Property(str, lambda s: sys.platform, constant=True)

    # Hotkey hint for the last page
    @Property(str, constant=True)
    def hotkey(self) -> str:
        from ..core import config
        return config.load().get("hotkey", "")

    # Start the work in the background (QML calls this from the main button)
    @Slot()
    def start(self) -> None:
        if self._state == "working":
            return
        self._set(state="working", progress=0.0, error="")
        threading.Thread(target=self._work, daemon=True).start()

    # Open the installed app's panel (button on the last page)
    @Slot()
    def openClipio(self) -> None:
        from .. import ipc
        ipc.send("show", 1500)

    # Run each step, publishing its name and the overall progress
    def _work(self) -> None:
        steps = UNINSTALL_STEPS if self._mode == "uninstall" else self._install_steps()
        try:
            for i, (label, fn) in enumerate(steps):
                self._set(step=label, progress=i / len(steps))
                t0 = time.monotonic()
                fn()
                time.sleep(max(0.0, MIN_STEP_S - (time.monotonic() - t0)))
            self._set(progress=1.0, state="done", step="")
        except Exception as e:   # shown on the page; the user can try again
            self._set(state="failed", error=str(e) or type(e).__name__)

    # Install steps for this computer (Linux helpers and the final start included)
    def _install_steps(self) -> list:
        steps = list(INSTALL_STEPS)
        if install.missing_helpers():
            steps.append(("Getting helper tools", self._helpers))
        steps.append(("Starting Clipio", install.launch))
        return steps

    # Install Linux helper tools and remember what is still missing
    def _helpers(self) -> None:
        self._set(missing=install.install_helpers())

    # Change some fields and tell QML (signals cross threads safely)
    def _set(self, **kw) -> None:
        for k, v in kw.items():
            setattr(self, "_" + k, v)
        self.changed.emit()


# Install (or uninstall) without a window; returns the exit code
def run_silent(uninstall: bool = False) -> int:
    steps = UNINSTALL_STEPS if uninstall else INSTALL_STEPS + [("Starting Clipio", install.launch)]
    try:
        for _, fn in steps:
            fn()
    except Exception as e:
        print(f"clipio setup failed: {e}", file=sys.stderr)
        return 1
    return 0


# Show the setup window until the user closes it
def run_setup(uninstall: bool = False) -> int:
    from PySide6.QtGui import QGuiApplication, QIcon
    from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonInstance

    app = QGuiApplication(sys.argv[:1])
    app.setApplicationName("Clipio Setup")
    app.setDesktopFileName("clipio")
    app.setWindowIcon(QIcon(str(UI.parent / "assets" / "clipio.svg")))
    controller = SetupController(uninstall)
    # the shared components folder also holds Store.qml, which imports the panel's `Clipio` module;
    # an empty stand-in lets the folder load (the setup window never uses Store)
    stand_in = QObject()
    qmlRegisterSingletonInstance(QObject, "Clipio", 1, 0, "Backend", stand_in)
    engine = QQmlApplicationEngine()
    engine.setInitialProperties({"setup": controller})
    engine.load(str(UI))
    if not engine.rootObjects():
        return 1
    return app.exec()
