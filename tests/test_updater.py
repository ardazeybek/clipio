"""Automatic updates: version compare, release lookup, verified download, markers and cleanup."""
import hashlib
import io
import json

import pytest

from clipio import __version__
from clipio.system import updater


# Fake network: maps URLs to bytes (or an exception)
@pytest.fixture
def net(monkeypatch, tmp_path):
    monkeypatch.setenv("CLIPIO_DATA_DIR", str(tmp_path / "data"))
    pages: dict = {}

    def fake_open(url):
        body = pages[url]
        if isinstance(body, Exception):
            raise body
        return io.BytesIO(body)
    monkeypatch.setattr(updater, "_open", fake_open)
    return pages


# Make a release with this computer's file and its checksum
def release(pages, version, payload=b"installer", good_sum=True):
    name = updater.asset_name()
    digest = hashlib.sha256(payload if good_sum else b"other").hexdigest()
    pages[updater.API] = json.dumps({"tag_name": "v" + version, "assets": [
        {"name": name, "browser_download_url": "https://x/" + name},
        {"name": "SHA256SUMS", "browser_download_url": "https://x/sums"}]}).encode()
    pages["https://x/" + name] = payload
    pages["https://x/sums"] = f"{digest}  {name}\n{'0' * 64}  other-file\n".encode()


# Versions compare by number, not as text
def test_parse_version():
    assert updater.parse_version("v0.10.0") > updater.parse_version("0.9.9")
    assert updater.parse_version("1.2") == (1, 2, 0)


# Only newer releases count; network errors mean "no update"
def test_check(net):
    release(net, "999.0.0")
    assert updater.check().version == "999.0.0"
    release(net, __version__)
    assert updater.check() is None
    net[updater.API] = OSError("offline")
    assert updater.check() is None


# The download is kept only when its checksum matches
def test_download_verified(net):
    release(net, "999.0.0")
    f = updater.download(updater.check())
    assert f and f.read_bytes() == b"installer"
    release(net, "999.0.1", good_sum=False)
    assert updater.download(updater.check()) is None
    assert not any(p.suffix == ".part" for p in updater.update_dir().rglob("*"))


# The "updated" marker is read once; an unchanged version does not count
def test_marker(net):
    updater.paths.ensure_dirs()
    updater.marker_file().write_text("0.0.1")
    assert updater.take_marker() == "0.0.1"
    assert updater.take_marker() == ""
    updater.marker_file().write_text(__version__)
    assert updater.take_marker() == ""


# Downloads of installed or older versions are deleted
def test_clean_old(net):
    for v in ("0.0.1", __version__, "999.0.0"):
        (updater.update_dir() / v).mkdir(parents=True)
    updater.clean_old()
    assert [p.name for p in updater.update_dir().iterdir()] == ["999.0.0"]
