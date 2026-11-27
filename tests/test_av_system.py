"""Bug-hunt probes for clipio/system and clipio/setup (OS calls mocked)."""
import io
from email.message import Message

import pytest

from clipio.setup import install
from clipio.system import hotkey, linktitle, updater


# hotkey.parse must reject function keys Windows/X11 do not have (F0, F25+)
@pytest.mark.parametrize("spec", ["ctrl+f0", "ctrl+f25", "ctrl+f99"])
def test_hotkey_parse_rejects_bad_function_keys(spec):
    with pytest.raises(ValueError):
        hotkey.parse(spec)


# hotkey.parse keeps F1 and F24 valid
def test_hotkey_parse_accepts_f1_f24():
    assert hotkey.parse("ctrl+f1")[1] == "f1"
    assert hotkey.win_vk(hotkey.parse("ctrl+f24")[1]) == 0x87


class _Resp(io.BytesIO):
    """Fake HTTP response with headers."""
    def __init__(self, body, ctype):
        super().__init__(body)
        self.headers = Message()
        self.headers["Content-Type"] = ctype

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


# linktitle.fetch must not raise on an unknown charset from the server
def test_linktitle_fetch_unknown_charset(monkeypatch):
    monkeypatch.setattr(linktitle.urllib.request, "urlopen",
                        lambda req, timeout: _Resp(b"<title>Hi</title>", "text/html; charset=bogus-xyz"))
    assert linktitle.fetch("example.com") == "Hi"


# updater._expected_hash matches "*name" binary lines and ignores other files
def test_updater_expected_hash_variants():
    sums = "AAA  other\nBBB *Clipio-Setup-Linux\n"
    assert updater._expected_hash(sums, "Clipio-Setup-Linux") == "bbb"
    assert updater._expected_hash(sums, "Clipio-Setup") == ""


# updater.parse_version orders versions numerically
def test_updater_parse_version_order():
    assert updater.parse_version("v1.10.0") > updater.parse_version("1.9.9")
    assert updater.parse_version("") == (0, 0, 0)


# install: a pipx `clipio` symlink in ~/.local/bin must survive install and uninstall
def test_install_linux_entries_keep_foreign_symlink(tmp_path, monkeypatch):
    monkeypatch.setattr(install.Path, "home", lambda: tmp_path)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "share"))
    pipx = tmp_path / "pipx" / "clipio"
    pipx.parent.mkdir()
    pipx.write_text("#!/bin/sh\n")
    link = tmp_path / ".local" / "bin" / "clipio"
    link.parent.mkdir(parents=True)
    link.symlink_to(pipx)
    install._linux_entries(str(install.target_dir() / "clipio"))
    assert link.resolve() == pipx.resolve()
    install._linux_remove_entries()
    assert link.is_symlink() and link.resolve() == pipx.resolve()


# install: our own link is created, replaced when dangling and removed on uninstall
def test_install_linux_entries_own_link(tmp_path, monkeypatch):
    monkeypatch.setattr(install.Path, "home", lambda: tmp_path)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "share"))
    link = tmp_path / ".local" / "bin" / "clipio"
    link.parent.mkdir(parents=True)
    link.symlink_to(tmp_path / "gone")
    exe = str(install.target_dir() / "clipio")
    install._linux_entries(exe)
    assert str(link.readlink()) == exe
    install._linux_remove_entries()
    assert not link.is_symlink()
