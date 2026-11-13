"""The `Backend` object the QML panel talks to: current state plus the actions it can ask for."""
import json

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import qmlRegisterSingletonInstance

_shared = None


class Bridge(QObject):
    """Holds the state shown in the panel; actions are forwarded to the app controller."""
    stateChanged = Signal()
    shownChanged = Signal()
    created = Signal(int)                 # a new item was made inside Clipio (edit, convert, OCR)
    notice = Signal(str)                  # short message for the panel (e.g. "No text found")
    _workerDone = Signal(str, int, str)   # background result: kind, item id, text (thread -> main)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ctl = None
        self._state = "{}"
        self._shown = False
        self._workerDone.connect(self._on_worker_done)

    # Hand a background thread's result to the main thread (safe to call from any thread)
    def post(self, kind: str, item_id: int, text: str) -> None:
        self._workerDone.emit(kind, item_id, text)

    # Runs in the main thread with a background result
    @Slot(str, int, str)
    def _on_worker_done(self, kind: str, item_id: int, text: str) -> None:
        if self._ctl:
            self._ctl.worker_done(kind, item_id, text)

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

    # Paste an item with tidied text (no tracking parameters, no extra whitespace)
    @Slot(int)
    def activateClean(self, item_id: int) -> None:
        self._ctl.activate(item_id, True, clean_it=True)

    # Paste the given items one after another (first now, the rest with `clipio next`)
    @Slot("QVariantList")
    def startQueue(self, ids) -> None:
        self._ctl.start_queue([int(i) for i in ids])

    # Paste the next queued item
    @Slot()
    def pasteNext(self) -> None:
        self._ctl.paste_next()

    # Forget the paste queue
    @Slot()
    def clearQueue(self) -> None:
        self._ctl.clear_queue()

    # Save edited text as an item and paste (or only copy) it
    @Slot(str, bool)
    def pasteEdited(self, text: str, paste: bool) -> None:
        self._ctl.paste_edited(text, paste)

    # Whole text of an item (cards only carry a preview)
    @Slot(int, result=str)
    def fullText(self, item_id: int) -> str:
        return self._ctl.full_text(item_id)

    # Conversions that work on an item (names)
    @Slot(int, result="QVariantList")
    def conversions(self, item_id: int):
        return self._ctl.conversions(item_id)

    # Convert an item; the result becomes a new item
    @Slot(int, str)
    def convert(self, item_id: int, name: str) -> None:
        self._ctl.convert(item_id, name)

    # Read the text in an image item (OCR); the text becomes a new item
    @Slot(int)
    def ocr(self, item_id: int) -> None:
        self._ctl.ocr(item_id)

    # Put an item in a folder ('' takes it out)
    @Slot(int, str)
    def setTag(self, item_id: int, tag: str) -> None:
        self._ctl.set_tag(item_id, tag)

    # Stop or start saving copies from an app
    @Slot(str, bool)
    def setAppIgnored(self, app: str, ignored: bool) -> None:
        self._ctl.set_app_ignored(app, ignored)

    # Turn an on/off setting on or off
    @Slot(str, bool)
    def setSwitch(self, key: str, on: bool) -> None:
        self._ctl.set_switch(key, on)

    # Change one panel shortcut ('' = default)
    @Slot(str, str)
    def setShortcut(self, action: str, keys: str) -> None:
        self._ctl.set_shortcut(action, keys)

    # Put every panel shortcut back to its default
    @Slot()
    def resetShortcuts(self) -> None:
        self._ctl.reset_shortcuts()

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

    # Change how many minutes the closed panel stays loaded (0 = free its memory at once)
    @Slot(int)
    def setPanelKeep(self, minutes: int) -> None:
        self._ctl.set_panel_keep(minutes)

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
