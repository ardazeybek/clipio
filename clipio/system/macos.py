"""Small macOS helpers through the Objective-C runtime (no extra packages needed)."""
import ctypes
import ctypes.util
import subprocess

_objc = None


# Load libobjc and AppKit once; return None when unavailable
def _runtime():
    global _objc
    if _objc is None:
        try:
            _objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
            ctypes.cdll.LoadLibrary("/System/Library/Frameworks/AppKit.framework/AppKit")
            _objc.objc_getClass.restype = ctypes.c_void_p
            _objc.objc_getClass.argtypes = [ctypes.c_char_p]
            _objc.sel_registerName.restype = ctypes.c_void_p
            _objc.sel_registerName.argtypes = [ctypes.c_char_p]
        except (OSError, TypeError, AttributeError):
            _objc = False
    return _objc or None


# Send an Objective-C message with exact argument and return types
def _send(obj, selector: str, *args, restype=ctypes.c_void_p, argtypes=()):
    rt = _runtime()
    if rt is None or not obj:
        return None
    proto = ctypes.CFUNCTYPE(restype, ctypes.c_void_p, ctypes.c_void_p, *argtypes)
    fn = proto(ctypes.cast(rt.objc_msgSend, ctypes.c_void_p).value)
    return fn(obj, rt.sel_registerName(selector.encode()), *args)


# Return an Objective-C class pointer
def _cls(name: str):
    rt = _runtime()
    return rt.objc_getClass(name.encode()) if rt else None


# The shared NSApplication instance
def _app():
    return _send(_cls("NSApplication"), "sharedApplication")


# Current pasteboard change counter (None when unavailable)
def change_count() -> int | None:
    board = _send(_cls("NSPasteboard"), "generalPasteboard")
    return _send(board, "changeCount", restype=ctypes.c_long) if board else None


# Run without a Dock icon (accessory app)
def hide_dock_icon() -> None:
    _send(_app(), "setActivationPolicy:", 1, restype=ctypes.c_bool, argtypes=(ctypes.c_long,))


# Bring Clipio to the front so its window gets keyboard focus
def activate() -> None:
    _send(_app(), "activateIgnoringOtherApps:", True, restype=None, argtypes=(ctypes.c_bool,))


# Hide Clipio so the previously active app gets focus back
def hide() -> None:
    _send(_app(), "hide:", None, restype=None, argtypes=(ctypes.c_void_p,))


# Name of the frontmost app (empty when unknown)
def frontmost_app() -> str:
    try:
        asn = subprocess.run(["lsappinfo", "front"], capture_output=True, text=True, timeout=2).stdout.strip()
        out = subprocess.run(["lsappinfo", "info", "-only", "name", asn],
                             capture_output=True, text=True, timeout=2).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return out.rsplit("=", 1)[-1].strip().strip('"') if "=" in out else ""


# Press Cmd+V in the frontmost app (needs the Accessibility permission)
def send_paste() -> bool:
    script = 'tell application "System Events" to keystroke "v" using command down'
    try:
        return subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False
