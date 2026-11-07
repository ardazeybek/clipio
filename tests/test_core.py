"""Storage, classification, settings, limits and paths: the platform-independent core."""
import sys
import time
from pathlib import Path

import pytest

from clipio.core import actions, classify, config, db, export, ingest, maintenance, paths
from clipio.core.ingest import Snapshot


# Save a text snapshot and return its id
def add_text(con, text, source="editor", cfg=None):
    return ingest.capture(con, Snapshot(formats=["text/plain"], text=text.encode()), source, cfg or config.load())


@pytest.mark.parametrize("text,kind,meta", [
    ("#E58F6F", "color", "#E58F6F"),
    ("rgb(1, 2, 3)", "color", "rgb(1, 2, 3)"),
    ("https://www.example.com/a?b=1", "url", "example.com"),
    ("www.example.org", "url", "example.org"),
    ("someone@example.com", "email", "example.com"),
    ("def f():\n    x = 1\n    return x\n", "code", ""),
    ("just a sentence", "text", ""),
])
def test_classify(text, kind, meta):
    assert classify.classify(text) == (kind, meta)


def test_paths_follow_overrides(tmp_path):
    assert paths.data_dir() == tmp_path / "data"
    assert paths.config_dir() == tmp_path / "config"
    assert paths.db_file().name == "clipio.db"


@pytest.mark.parametrize("platform,env,expected", [
    ("win32", {"LOCALAPPDATA": "/w/local", "APPDATA": "/w/roam"}, ("/w/local/clipio", "/w/roam/clipio")),
    ("linux", {"XDG_DATA_HOME": "/x/data", "XDG_CONFIG_HOME": "/x/cfg"}, ("/x/data/clipio", "/x/cfg/clipio")),
])
def test_paths_per_platform(monkeypatch, platform, env, expected):
    monkeypatch.delenv("CLIPIO_DATA_DIR")
    monkeypatch.delenv("CLIPIO_CONFIG_DIR")
    monkeypatch.setattr(sys, "platform", platform)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    assert (paths.data_dir(), paths.config_dir()) == (Path(expected[0]), Path(expected[1]))


def test_paths_macos(monkeypatch):
    monkeypatch.delenv("CLIPIO_DATA_DIR")
    monkeypatch.setattr(sys, "platform", "darwin")
    assert paths.data_dir() == Path.home() / "Library" / "Application Support" / "clipio"


def test_config_defaults_template_and_set_int():
    assert config.load()["retention_days"] == 14
    config.write_default_if_missing()
    config.set_int("retention_days", 3)
    assert config.load()["retention_days"] == 3
    assert "# days before unpinned" in paths.config_file().read_text()
    config.set_int("max_items", 9)            # an existing key
    config.set_int("brand_new", 5)            # a missing key is appended
    cfg = config.load()
    assert cfg["max_items"] == 9 and cfg["brand_new"] == 5


def test_broken_config_falls_back_to_defaults():
    paths.config_file().parent.mkdir(parents=True)
    paths.config_file().write_text("this is = = not toml")
    assert config.load()["max_items"] == 500


def test_same_text_is_stored_once(con):
    a = add_text(con, "hello")
    b = add_text(con, "hello")
    assert a == b
    assert len(db.list_items(con)) == 1


def test_skip_rules(con):
    cfg = dict(config.load(), ignore_apps=["KeePassXC"])
    assert add_text(con, "secret", source="keepassxc", cfg=cfg) is None
    snap = Snapshot(formats=["text/plain", "x-kde-passwordManagerHint"], text=b"pw")
    assert ingest.capture(con, snap, "", cfg) is None
    actions.set_paused(True)
    assert add_text(con, "while paused") is None
    actions.set_paused(False)
    assert add_text(con, "after pause") is not None
    assert add_text(con, "   ") is None
    big = dict(cfg, max_text_kb=1)
    assert add_text(con, "x" * 2000, cfg=big) is None


def test_images_are_saved_to_disk(con):
    png = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + (7).to_bytes(4, "big") + (5).to_bytes(4, "big") + b"rest"
    item_id = ingest.capture(con, Snapshot(formats=["image/png"], image=png), "", config.load())
    row = db.get(con, item_id)
    assert (row["width"], row["height"]) == (7, 5)
    assert (paths.image_dir() / row["image_file"]).read_bytes() == png
    db.delete(con, item_id)
    assert not (paths.image_dir() / row["image_file"]).exists()


def test_pinned_first_and_clear_keeps_pins(con):
    a = add_text(con, "first")
    add_text(con, "second")
    actions.toggle_pin(con, a)
    assert db.list_items(con)[0]["id"] == a
    assert actions.clear(con) == 1
    assert [r["id"] for r in db.list_items(con)] == [a]


def test_retention_and_limits(con):
    old = add_text(con, "old")
    con.execute("UPDATE items SET used=? WHERE id=?", (time.time() - 10 * 86400, old))
    con.commit()
    for i in range(5):
        add_text(con, f"item {i}")
    assert actions.set_retention(con, 7) == 7
    assert db.get(con, old) is None
    maintenance.run(con, dict(config.load(), max_items=2))
    assert len(db.list_items(con)) == 2
    assert actions.set_retention(con, 0) == 1 and actions.set_retention(con, 999) == 365


def test_copy_puts_item_back(con, fake_clipboard):
    item_id = add_text(con, "copy me")
    assert actions.copy(con, fake_clipboard, item_id)
    assert fake_clipboard.text == "copy me"
    assert not actions.copy(con, fake_clipboard, 12345)


def test_state_export(con):
    add_text(con, "https://example.com")
    state = export.build_state(con)
    assert state["total"] == 1 and state["retention_days"] == 14 and not state["paused"]
    item = state["items"][0]
    assert item["hint"] == "url" and item["preview"] == "https://example.com"
