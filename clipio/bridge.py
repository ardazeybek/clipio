"""The `Backend` object the QML panel talks to: current state plus the actions it can ask for."""
import json

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import qmlRegisterSingletonInstance

_shared = None


class Bridge(QObject):
    """Holds the state shown in the panel; actions are forwarded to the app controller."""
    stateChanged = Signal()
    shownChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ctl = None
        self._state = "{}"
        self._shown = False

    # Connect the bridge to the controller that carries out the actions
    def attach(self, controller) -> None:
        self._ctl = controller
        self._shown = False

    # Replace the state shown in the panel
    def set_state(self, state: dict) -> None:
        self._state = json.dumps(state, ensure_ascii=False)
        self.stateChanged.emit()

    # Tell the panel to play its open or close animation
    def set_shown(self, shown: bool) -> None:
        if shown != self._shown:
            self._shown = shown
            self.shownChanged.emit()

    # JSON text of the current state
    def _get_state(self) -> str:
        return self._state

    # True while the panel is open
    def _get_shown(self) -> bool:
        return self._shown

    stateJson = Property(str, _get_state, notify=stateChanged)
    shown = Property(bool, _get_shown, notify=shownChanged)

    # ---- actions called from QML ----

    # Paste an item into the previous app, or only copy it
    @Slot(int, bool)
    def activate(self, item_id: int, paste: bool) -> None:
        self._ctl.activate(item_id, paste)

    # Pin or unpin an item
    @Slot(int)
    def togglePin(self, item_id: int) -> None:
        self._ctl.toggle_pin(item_id)

    # Delete an item
    @Slot(int)
    def remove(self, item_id: int) -> None:
        self._ctl.delete(item_id)

    # Delete every unpinned item
    @Slot()
    def clearAll(self) -> None:
        self._ctl.clear()

    # Pause or resume recording
    @Slot(bool)
    def setPaused(self, paused: bool) -> None:
        self._ctl.set_paused(paused)

    # Change how many days items are kept
    @Slot(int)
    def setRetention(self, days: int) -> None:
        self._ctl.set_retention(days)

    # Send fresh state to the panel
    @Slot()
    def refresh(self) -> None:
        self._ctl.refresh()

    # Close the panel
    @Slot()
    def requestHide(self) -> None:
        self._ctl.hide()

    # The window lost focus (the user clicked elsewhere)
    @Slot()
    def focusLost(self) -> None:
        self._ctl.focus_lost()


# The one Bridge of this process, registered as the QML singleton `Backend`
# (Qt breaks if it is registered again once a QML engine exists)
def shared() -> Bridge:
    global _shared
    if _shared is None:
        _shared = Bridge()
        qmlRegisterSingletonInstance(Bridge, "Clipio", 1, 0, "Backend", _shared)
    return _shared
