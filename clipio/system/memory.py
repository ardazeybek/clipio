"""Gives freed memory back to the operating system so the background service stays small."""
import ctypes
import ctypes.util
import gc
import sys


# Collect Python garbage and ask the C allocator to return free pages (best effort on every OS)
def trim() -> None:
    gc.collect()
    try:
        if sys.platform.startswith("linux"):
            _trim_linux()
        elif sys.platform == "darwin":
            _trim_macos()
        elif sys.platform == "win32":
            _trim_windows()
    except (OSError, AttributeError, TypeError, ValueError):
        pass   # musl, sandboxed or unusual systems: nothing to do


# glibc keeps freed memory in its heap; malloc_trim hands it back
def _trim_linux() -> None:
    libc = ctypes.CDLL(ctypes.util.find_library("c") or "libc.so.6")
    if hasattr(libc, "malloc_trim"):
        libc.malloc_trim(0)


# macOS: release free pages of every malloc zone
def _trim_macos() -> None:
    libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib")
    libc.malloc_zone_pressure_relief.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    libc.malloc_zone_pressure_relief(None, 0)


# Windows: let the system page out memory the service is not using right now
def _trim_windows() -> None:
    from ctypes import wintypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    k32.SetProcessWorkingSetSize.argtypes = [wintypes.HANDLE, ctypes.c_size_t, ctypes.c_size_t]
    k32.SetProcessWorkingSetSize(k32.GetCurrentProcess(), ctypes.c_size_t(-1), ctypes.c_size_t(-1))
