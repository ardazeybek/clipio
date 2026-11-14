"""Setup logic of the packaged app: install folder, copying, launcher entries, removal, wizard texts."""
import sys
from pathlib import Path

import pytest

from clipio.setup import install


# Pretend to be the packaged setup file: a fake unpacked bundle with a payload launcher
@pytest.fixture
def fake_bundle(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("LOCALAPPDATA", str(home / "AppData" / "Local"))
    monkeypatch.setenv("APPDATA", str(home / "AppData" / "Roaming"))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    bundle = tmp_path / "meipass"
    (bundle / "payload").mkdir(parents=True)
    (bundle / "payload" / install.EXE).write_text("launcher")
    (bundle / "clipio" / "ui" / "assets").mkdir(parents=True)
    (bundle / "clipio" / "ui" / "assets" / "clipio.svg").write_text("<svg/>")
    (bundle / "libQt.so").write_text("qt")
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    return bundle


# The install folder is per user and needs no admin rights
def test_target_is_in_home(fake_bundle):
    if sys.platform == "darwin":
        assert install.target_dir().name == "Clipio.app"
    else:
        assert str(install.target_dir()).startswith(str(Path.home()))


@pytest.mark.skipif(sys.platform == "darwin", reason="macOS copies the .app bundle instead")
# Copying puts the launcher next to _internal (without the payload) and records the version
def test_copy_files_and_update(fake_bundle):
    install.copy_files()
    dest = install.target_dir()
    assert (dest / install.EXE).read_text() == "launcher"
    assert (dest / "_internal" / "libQt.so").exists()
    assert not (dest / "_internal" / "payload").exists()
    assert install.installed_version()
    # an update replaces the files and leaves no temporary folders behind
    (fake_bundle / "libQt.so").write_text("qt2")
    install.copy_files()
    assert (dest / "_internal" / "libQt.so").read_text() == "qt2"
    assert sorted(p.name for p in dest.parent.iterdir()) == [dest.name]


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux launcher entries")
# Linux: launcher entry, icon and command link are written and removed again
def test_linux_entries(fake_bundle):
    install.copy_files()
    install.add_shortcuts()
    desktop, icon, link = install._linux_paths()
    assert "Exec=" in desktop.read_text() and icon.exists() and link.is_symlink()
    install._linux_remove_entries()
    assert not desktop.exists() and not icon.exists() and not link.exists()


# Removing deletes the app but not the user's history
def test_uninstall_keeps_data(fake_bundle, monkeypatch, tmp_path):
    monkeypatch.setattr(install, "stop_running", lambda: None)
    monkeypatch.setattr(install.autostart, "set_enabled", lambda on, exe=None: None)
    if sys.platform == "win32":
        monkeypatch.setattr(install, "_windows_remove_entries", lambda: None)
    dest = install.target_dir()
    dest.mkdir(parents=True)
    (dest / install.EXE).write_text("x")
    data = tmp_path / "data.db"
    data.write_text("history")
    install.uninstall()
    assert not dest.exists() and data.exists()


# The wizard picks its mode from what is installed
def test_wizard_modes(fake_bundle):
    from clipio.setup.window import SetupController
    assert SetupController().mode == "install"
    if sys.platform != "darwin":
        install.copy_files()
        assert SetupController().mode == "update"
    assert SetupController(uninstall=True).mode == "uninstall"


# The autostart entry can point at the installed app
def test_autostart_uses_installed_exe():
    from clipio.system import autostart
    assert autostart.command("/opt/Clipio/clipio") == ["/opt/Clipio/clipio", "run"]
    assert '"/my apps/clipio" run' in autostart.linux_desktop_text("/my apps/clipio")
