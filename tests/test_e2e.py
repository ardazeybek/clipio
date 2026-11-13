"""End to end: a real service process starts the panel process on demand, which quits when unused."""
import os
import subprocess
import sys
import time
import uuid

import pytest

from clipio import ipc


# Wait until check() is true (or the timeout passes); return its last value
def wait_for(check, timeout=30.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check():
            return True
        time.sleep(0.2)
    return check()


# Run a `clipio` command in its own process with the test's environment
def clipio(env, *args, timeout=60):
    return subprocess.run([sys.executable, "-m", "clipio", *args], env=env,
                          capture_output=True, text=True, timeout=timeout)


@pytest.fixture
def service(tmp_path, monkeypatch):
    name = "clipio-e2e-" + uuid.uuid4().hex[:8]
    monkeypatch.setenv("CLIPIO_IPC_NAME", name)
    (tmp_path / "config").mkdir()
    # no global hotkey (CI machines have no keyboard access), close the panel right away
    (tmp_path / "config" / "config.toml").write_text('hotkey = "none"\npanel_keep_minutes = 0\n')
    env = dict(os.environ, CLIPIO_IPC_NAME=name, QT_QPA_PLATFORM="offscreen",
               CLIPIO_DATA_DIR=str(tmp_path / "data"), CLIPIO_CONFIG_DIR=str(tmp_path / "config"))
    proc = subprocess.Popen([sys.executable, "-m", "clipio", "run"], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert wait_for(ipc.is_running), "the service did not start"
    yield env, proc
    clipio(env, "stop")
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
    ipc.send("quit", 500, ipc.PANEL)


def test_panel_starts_on_demand_and_frees_itself(service):
    env, proc = service
    assert not ipc.is_running(ipc.PANEL), "the panel must not be loaded before it is opened"
    assert clipio(env, "show").returncode == 0
    assert wait_for(lambda: ipc.is_running(ipc.PANEL)), "the panel process did not start"
    assert clipio(env, "hide").returncode == 0
    assert wait_for(lambda: not ipc.is_running(ipc.PANEL)), "the closed panel did not quit"
    # opening again starts a fresh panel process
    assert clipio(env, "toggle").returncode == 0
    assert wait_for(lambda: ipc.is_running(ipc.PANEL))
    # stopping Clipio also closes the open panel
    clipio(env, "stop")
    assert proc.wait(timeout=20) == 0
    assert wait_for(lambda: not ipc.is_running(ipc.PANEL))


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="reads /proc")
def test_service_does_not_load_the_ui_libraries(service):
    _, proc = service
    maps = open(f"/proc/{proc.pid}/maps").read()
    assert "libQt6Quick" not in maps and "libQt6Qml." not in maps
