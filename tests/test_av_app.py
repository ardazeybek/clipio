"""Bug-hunt probes for the service, panel link, panel process, IPC and QML panel."""
import os
import subprocess
import sys
import textwrap
import time

import pytest

from clipio import ipc, panel_link


# Spin the Qt event loop until `done()` or the time runs out
def spin(app, done, ms=2000):
    end = time.monotonic() + ms / 1000
    while not done() and time.monotonic() < end:
        app.processEvents()


# Hidden panel (empty list, so the swaying logo is shown) must not keep animations running
def test_panel_hidden_has_no_running_animations(tmp_path):
    script = textwrap.dedent("""
        import sys
        from PySide6.QtCore import QTimer, QObject
        from PySide6.QtGui import QGuiApplication
        from clipio.app import create_application
        from clipio.panel import PanelController
        from clipio.core import paths
        paths.ensure_dirs()
        app = create_application(sys.argv[:1], QGuiApplication)
        ctl = PanelController(app, service=lambda c: "")
        assert ctl.load_ui()
        def pump(ms):
            d = []; QTimer.singleShot(ms, lambda: d.append(1))
            while not d: app.processEvents()
        def running():
            return [o.metaObject().className() for o in ctl.window.findChildren(QObject)
                    if "Animation" in o.metaObject().className() and o.property("running")]
        ctl.show(); pump(700)
        assert running(), "logo should sway while open"
        ctl.hide(); pump(700)
        print("RUNNING", running())
    """)
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", CLIPIO_IPC_NAME=f"av{os.getpid()}")
    out = subprocess.run([sys.executable, "-c", script], env=env, capture_output=True,
                         text=True, timeout=60)
    assert out.returncode == 0, out.stderr[-800:]
    assert "RUNNING []" in out.stdout, out.stdout


# ---- PanelLink ----

# A spawned panel that has not reported yet blocks a second spawn
def test_panel_link_show_twice_spawns_once(monkeypatch):
    spawned = []
    link = panel_link.PanelLink()
    monkeypatch.setattr(link, "_spawn", lambda: (spawned.append(1), setattr(link, "_starting_since", time.monotonic())))
    link.show()
    link.show()
    assert spawned == [1]


# "ready" keeps the open state; "exit" and unknown states
def test_panel_link_report_states():
    link = panel_link.PanelLink()
    assert link.report("shown") == "ok" and link.shown and link.running
    assert link.report("ready") == "ok" and link.shown
    assert link.report("hidden") == "ok" and not link.shown and link.running
    assert link.report("exit") == "ok" and not link.running
    assert link.report("bogus") == "unknown command"


# hide/refresh do nothing while no panel runs
def test_panel_link_idle_commands_without_panel(monkeypatch):
    posted = []
    monkeypatch.setattr(ipc, "post", lambda *a, **k: posted.append(a))
    link = panel_link.PanelLink()
    link.hide(); link.refresh()
    assert posted == []


# ---- IPC ----

# send gets the reply; post delivers a line without waiting; post to nobody calls on_fail
def test_ipc_send_post_and_fail(qapp, monkeypatch):
    monkeypatch.setenv("CLIPIO_IPC_NAME", f"avipc{os.getpid()}")
    got = []
    server = ipc.Server(lambda line: (got.append(line), "pong" if line == "ping" else "ok")[1])
    assert server.listen()
    try:
        failed = []
        ipc.post("hello world")
        ipc.post("x", role=ipc.PANEL, on_fail=lambda: failed.append(1))
        spin(qapp, lambda: "hello world" in got and failed)
        assert "hello world" in got and failed == [1]
        assert not ipc._pending or all(s is not None for s in ipc._pending)
    finally:
        server.close()


# Long socket names are shortened to fit macOS' limit and stay unique per role
def test_ipc_server_name_long(monkeypatch):
    monkeypatch.setenv("CLIPIO_IPC_NAME", "x" * 60)
    a, b = ipc.server_name(), ipc.server_name(ipc.PANEL)
    assert len(a) <= ipc.MAX_NAME and len(b) <= ipc.MAX_NAME and a != b


# ---- service commands ----

@pytest.fixture
def svc(qapp, fake_clipboard):
    from PySide6.QtCore import QObject, Signal
    from clipio.app import Controller

    class Clip(QObject):
        changed = Signal()
        def read(self): return fake_clipboard.read()
        def write_text(self, t): fake_clipboard.write_text(t)
        def write_image(self, d, m): fake_clipboard.write_image(d, m)
        def stop(self): pass

    class Link:
        shown = False
        running = False
        def refresh(self): pass
        def report(self, s): return "ok"
        def hide(self): pass
    return Controller(qapp, Clip(), panel=Link())


# Malformed commands are rejected, not crashing
def test_controller_handle_command_parsing(svc):
    assert svc.handle_command("ping") == "pong"
    assert svc.handle_command("activate 1 x 0") == "unknown command"
    assert svc.handle_command("paste abc") == "unknown command"
    assert svc.handle_command("activate 999 0 0") == "failed"
    assert svc.handle_command("queue?") == ""
    assert svc.handle_command("") == "unknown command"


# The queue skips deleted ids and paste_next on an empty queue is a no-op
def test_controller_queue_skips_missing(svc, monkeypatch):
    from clipio.core import actions
    a = actions.save_text(svc.con, "one")
    b = actions.save_text(svc.con, "two")
    pasted = []
    monkeypatch.setattr(svc, "activate", lambda i, p, c=False: pasted.append(i) or True)
    svc.start_queue([a, 12345, b])
    assert pasted == [a] and svc.queue == [b]
    svc.paste_next(); svc.paste_next()
    assert pasted == [a, b] and svc.queue == []
