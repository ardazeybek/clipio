"""Small Windows helpers through the Win32 API (ctypes, no extra packages needed)."""
import ctypes
import os
import sys

if sys.platform == "win32":
    from ctypes import wintypes
    _user32 = ctypes.WinDLL("user32", use_last_error=True)
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _user32.GetForegroundWindow.restype = wintypes.HWND
    _user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    _user32.BringWindowToTop.argtypes = [wintypes.HWND]
    _user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    _user32.AllowSetForegroundWindow.argtypes = [wintypes.DWORD]
    _user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                     wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]

VK_CONTROL, VK_V = 0x11, 0x56
KEYEVENTF_KEYUP = 0x0002
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


# Handle of the window that currently has focus (0 when none)
def foreground_window() -> int:
    return _user32.GetForegroundWindow() or 0


# Give focus back to a window
def focus_window(hwnd: int) -> bool:
    return bool(hwnd) and bool(_user32.SetForegroundWindow(hwnd))


# Bring one of Clipio's own windows to the front, even when Windows' focus lock refuses at first
def force_focus(hwnd: int) -> bool:
    if not hwnd or focus_window(hwnd):
        return bool(hwnd)
    # attach to the thread that has focus now, so Windows lets this thread take it over
    fg_thread = _user32.GetWindowThreadProcessId(_user32.GetForegroundWindow(), None)
    own_thread = _kernel32.GetCurrentThreadId()
    attached = fg_thread and fg_thread != own_thread and _user32.AttachThreadInput(own_thread, fg_thread, True)
    try:
        _user32.BringWindowToTop(hwnd)
        return focus_window(hwnd)
    finally:
        if attached:
            _user32.AttachThreadInput(own_thread, fg_thread, False)


# Let another process (the panel) take focus; the service may grant it after a hotkey or tray click
def allow_foreground() -> None:
    _user32.AllowSetForegroundWindow(0xFFFFFFFF)   # ASFW_ANY


# Program name of the process that owns a window, e.g. "notepad" (empty when unknown)
def process_name(hwnd: int) -> str:
    if not hwnd:
        return ""
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    handle = _kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(1024)
        buf = ctypes.create_unicode_buffer(size.value)
        if not _kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return ""
        return os.path.splitext(os.path.basename(buf.value))[0]
    finally:
        _kernel32.CloseHandle(handle)


# Press Ctrl+V in the focused window
def send_paste() -> bool:
    for vk, flags in ((VK_CONTROL, 0), (VK_V, 0), (VK_V, KEYEVENTF_KEYUP), (VK_CONTROL, KEYEVENTF_KEYUP)):
        _user32.keybd_event(vk, 0, flags, 0)
    return True
