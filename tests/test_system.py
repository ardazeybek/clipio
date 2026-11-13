"""Operating-system layer: desktop detection, hotkeys, paste commands, autostart, clipboard, IPC."""
import sys

import pytest

from clipio import system
from clipio.system import autostart, hotkey, paste

on_windows = pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
on_macos = pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")


@pytest.mark.parametrize("platform,env,expected", [
    ("win32", {}, "windows"),
    ("darwin", {}, "macos"),
    ("linux", {"WAYLAND_DISPLAY": "wayland-0"}, "wayland"),
    ("linux", {"WAYLAND_DISPLAY": "wayland-0", "QT_QPA_PLATFORM": "xcb"}, "x11"),
    ("linux", {}, "x11"),
])
def test_desktop_kind(monkeypatch, platform, env, expected):
    monkeypatch.setattr(sys, "platform", platform)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    assert system.kind() == expected


@pytest.mark.parametrize("spec,mods,key", [
    ("ctrl+shift+v", {"ctrl", "shift"}, "v"),
    ("Cmd + Shift + V", {"super", "shift"}, "v"),
    ("super+v", {"super"}, "v"),
    ("alt+f9", {"alt"}, "f9"),
])
def test_hotkey_parse(spec, mods, key):
    assert hotkey.parse(spec) == (frozenset(mods), key)


@pytest.mark.parametrize("bad", ["v", "ctrl+shift", "ctrl+v+b", "ctrl+space"])
def test_hotkey_rejects_bad_specs(bad):
    with pytest.raises(ValueError):
        hotkey.parse(bad)


def test_hotkey_formats():
    assert hotkey.to_pynput(*hotkey.parse("cmd+shift+v")) == "<shift>+<cmd>+v"
    assert hotkey.win_vk("v") == 0x56 and hotkey.win_vk("f1") == 0x70


def test_hotkey_is_off_on_wayland(monkeypatch, qapp):
    monkeypatch.setattr(system, "kind", lambda: "wayland")
    monkeypatch.setattr(hotkey, "kind", lambda: "wayland")
    assert hotkey.GlobalHotkey().start("super+v") is False


def test_paste_commands(monkeypatch):
    lua, classic = paste.hyprland_commands(["ctrl", "shift"])
    assert 'mods="CTRL SHIFT"' in lua[-1] and classic[-1] == "CTRL,SHIFT,V,activewindow"
    monkeypatch.setattr(paste.shutil, "which", lambda name: "/usr/bin/" + name)
    assert paste.generic_command("x11", ["ctrl"]) == ["xdotool", "key", "--clearmodifiers", "ctrl+v"]
    assert paste.generic_command("wayland", ["ctrl"]) == ["wtype", "-M", "ctrl", "v", "-m", "ctrl"]
    monkeypatch.setattr(paste.shutil, "which", lambda name: None)
    assert paste.generic_command("x11", ["ctrl"]) is None
    assert paste._linux_mods("kitty") == ["ctrl", "shift"] and paste._linux_mods("firefox") == ["ctrl"]


@pytest.mark.skipif(sys.platform == "win32", reason="file-based autostart")
def test_autostart_files(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    assert not autostart.is_enabled()
    autostart.set_enabled(True)
    assert autostart.is_enabled()
    f = autostart.mac_plist() if sys.platform == "darwin" else autostart.linux_desktop()
    assert "-m" in f.read_text() and "clipio" in f.read_text()
    autostart.set_enabled(False)
    assert not autostart.is_enabled()


def test_autostart_texts():
    assert "<key>RunAtLoad</key>" in autostart.mac_plist_text()
    assert autostart.linux_desktop_text().startswith("[Desktop Entry]")
    assert autostart.command()[-3:] == ["-m", "clipio", "run"]


@on_windows
def test_autostart_registry():
    before = autostart.is_enabled()
    autostart.set_enabled(True)
    assert autostart.is_enabled()
    autostart.set_enabled(before)


def test_qt_clipboard_roundtrip(qapp):
    from clipio.system.clipboard import QtClipboard
    cb = QtClipboard(qapp.clipboard())
    assert cb.write_text("clipio test ✓")
    qapp.processEvents()
    assert cb.read().text == "clipio test ✓".encode()


@on_windows
def test_windows_helpers():
    from clipio.system import windows
    hwnd = windows.foreground_window()
    assert isinstance(windows.process_name(hwnd), str)
    assert windows.process_name(0) == ""
    assert windows.force_focus(0) is False
    windows.allow_foreground()   # must not raise


@on_macos
def test_macos_helpers(qapp):
    from clipio.system import macos
    assert isinstance(macos.change_count(), int)
    macos.hide_dock_icon()
    assert isinstance(macos.frontmost_app(), str)


def test_ipc_roundtrip(qapp):
    """A `clipio` command in another process reaches the app and gets its reply."""
    import subprocess
    import time
    from clipio import ipc
    server = ipc.Server(lambda line: "echo:" + line)
    assert server.listen()
    client = subprocess.Popen(
        [sys.executable, "-c", "from clipio import ipc; print(ipc.send('hello there', 5000))"],
        stdout=subprocess.PIPE, text=True)
    deadline = time.monotonic() + 15
    while client.poll() is None and time.monotonic() < deadline:
        qapp.processEvents()
    server.close()
    if client.poll() is None:
        client.kill()
    assert client.communicate(timeout=5)[0].strip() == "echo:hello there"


def test_memory_trim_is_safe():
    from clipio.system import memory
    memory.trim()   # must never raise, on any OS


def test_ipc_post_reaches_server_without_waiting(qapp):
    """A fire-and-forget message arrives; posting to nobody calls on_fail."""
    import time
    from clipio import ipc
    got, failed = [], []
    server = ipc.Server(lambda line: got.append(line) or "ok", role="posttest")
    assert server.listen()
    ipc.post("panel shown", "posttest")
    ipc.post("hello", "nobody-listens", on_fail=lambda: failed.append(1))
    deadline = time.monotonic() + 5
    while (not got or not failed) and time.monotonic() < deadline:
        qapp.processEvents()
    server.close()
    assert got == ["panel shown"]
    assert failed == [1]


def test_panel_link_follows_panel_reports(monkeypatch):
    from clipio import panel_link
    spawned = []
    link = panel_link.PanelLink()
    monkeypatch.setattr(link, "_spawn", lambda: spawned.append(1))
    link.show()                         # nothing runs yet: start the panel process
    assert spawned == [1]
    assert link.report("ready") == "ok" and link.running and not link.shown
    link.report("shown")
    assert link.shown
    link.report("hidden")
    assert link.running and not link.shown
    link.report("exit")
    assert not link.running
    assert link.report("bogus") == "unknown command"


def test_panel_command_runs_the_panel():
    assert autostart.panel_command()[-3:] == ["-m", "clipio", "panel"]
