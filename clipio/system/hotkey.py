"""Global keyboard shortcut that opens the panel (Windows, macOS and X11).

On Wayland, apps cannot grab keys; bind `clipio toggle` in the compositor instead.
"""
import sys
import threading

from PySide6.QtCore import QObject, Signal

from . import kind

MODIFIERS = {"ctrl", "shift", "alt", "super"}
ALIASES = {"control": "ctrl", "cmd": "super", "command": "super", "win": "super",
           "meta": "super", "option": "alt"}


# Split "ctrl+shift+v" into ({"ctrl", "shift"}, "v"); raise ValueError when invalid
def parse(spec: str) -> tuple[frozenset, str]:
    parts = [ALIASES.get(p, p) for p in spec.lower().replace(" ", "").split("+") if p]
    mods = frozenset(p for p in parts if p in MODIFIERS)
    keys = [p for p in parts if p not in MODIFIERS]
    if len(keys) != 1 or not mods:
        raise ValueError(f"invalid hotkey: {spec!r} (use something like ctrl+shift+v)")
    key = keys[0]
    if not (len(key) == 1 and key.isalnum()) and not (key.startswith("f") and key[1:].isdigit()):
        raise ValueError(f"unsupported key in hotkey: {key!r}")
    return mods, key


# Turn a parsed hotkey into pynput's format, e.g. "<cmd>+<shift>+v"
def to_pynput(mods: frozenset, key: str) -> str:
    names = {"ctrl": "<ctrl>", "shift": "<shift>", "alt": "<alt>", "super": "<cmd>"}
    order = ["ctrl", "alt", "shift", "super"]
    k = f"<{key}>" if len(key) > 1 else key
    return "+".join([names[m] for m in order if m in mods] + [k])


# Win32 virtual-key code for a key name
def win_vk(key: str) -> int:
    if len(key) == 1:
        return ord(key.upper())
    return 0x6F + int(key[1:])   # F1 = 0x70


class GlobalHotkey(QObject):
    """Emits `activated` from any thread; Qt delivers it on the main thread."""
    activated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stopper = None

    # Start listening; return False when this desktop does not allow a global hotkey
    def start(self, spec: str) -> bool:
        try:
            mods, key = parse(spec)
        except ValueError as e:
            print(f"clipio: {e}", file=sys.stderr)
            return False
        k = kind()
        if k == "windows":
            return self._start_windows(mods, key)
        if k == "macos":
            return self._start_pynput(mods, key)
        if k == "x11":
            return self._start_x11(mods, key)
        return False

    # Windows: RegisterHotKey with its own message loop
    def _start_windows(self, mods, key) -> bool:
        import ctypes
        from ctypes import wintypes
        flags = {"alt": 0x1, "ctrl": 0x2, "shift": 0x4, "super": 0x8}
        mask = sum(flags[m] for m in mods) | 0x4000   # MOD_NOREPEAT
        ready, ok, tid = threading.Event(), [False], [0]

        # Register the hotkey and wait for WM_HOTKEY messages
        def loop():
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            tid[0] = ctypes.WinDLL("kernel32").GetCurrentThreadId()
            ok[0] = bool(user32.RegisterHotKey(None, 1, mask, win_vk(key)))
            ready.set()
            if not ok[0]:
                return
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == 0x0312:   # WM_HOTKEY
                    self.activated.emit()
            user32.UnregisterHotKey(None, 1)

        threading.Thread(target=loop, daemon=True).start()
        ready.wait(3)
        self._stopper = lambda: ctypes.WinDLL("user32").PostThreadMessageW(tid[0], 0x0012, 0, 0)
        return ok[0]

    # macOS: pynput (needs the Input Monitoring permission)
    def _start_pynput(self, mods, key) -> bool:
        try:
            from pynput import keyboard
        except ImportError:
            return False
        listener = keyboard.GlobalHotKeys({to_pynput(mods, key): self.activated.emit})
        listener.daemon = True
        listener.start()
        self._stopper = listener.stop
        return True

    # X11: XGrabKey on the root window through python-xlib
    def _start_x11(self, mods, key) -> bool:
        try:
            from Xlib import X, XK, display
        except ImportError:
            return False
        try:
            disp = display.Display()
        except Exception:
            return False
        flags = {"shift": X.ShiftMask, "ctrl": X.ControlMask, "alt": X.Mod1Mask, "super": X.Mod4Mask}
        mask = sum(flags[m] for m in mods)
        sym = XK.string_to_keysym(key.upper() if len(key) > 1 else key)
        code = disp.keysym_to_keycode(sym)
        if not code:
            return False
        root = disp.screen().root
        # also grab with Caps Lock / Num Lock on, which X11 treats as modifiers
        for extra in (0, X.LockMask, X.Mod2Mask, X.LockMask | X.Mod2Mask):
            root.grab_key(code, mask | extra, True, X.GrabModeAsync, X.GrabModeAsync)
        disp.sync()
        stop = threading.Event()

        # Read X events and emit on every matching key press
        def loop():
            while not stop.is_set():
                ev = disp.next_event()
                if ev.type == X.KeyPress and ev.detail == code:
                    self.activated.emit()

        threading.Thread(target=loop, daemon=True).start()
        self._stopper = stop.set
        return True

    # Stop listening
    def stop(self) -> None:
        if self._stopper:
            self._stopper()
            self._stopper = None
