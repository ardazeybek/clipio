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


# Wrong types and out-of-range numbers in config.toml fall back to safe values
def test_bad_config_values_are_corrected():
    paths.config_file().parent.mkdir(parents=True, exist_ok=True)
    paths.config_file().write_text('retention_days = 0\nmax_items = "lots"\npersist = 3\nignore_apps = "x"\n')
    cfg = config.load()
    assert cfg["retention_days"] == 1
    assert cfg["max_items"] == config.DEFAULTS["max_items"]
    assert cfg["persist"] is True
    assert cfg["ignore_apps"] == []


# Pasting an image whose file is gone removes the broken item
def test_copy_drops_item_with_missing_image(con):
    from conftest import FakeClipboard
    png = b"\x89PNG\r\n\x1a\n" + b"\0" * 16
    item_id = ingest.capture(con, Snapshot(image=png), "", config.load())
    (paths.image_dir() / db.get(con, item_id)["image_file"]).unlink()
    assert actions.copy(con, FakeClipboard(), item_id) is False
    assert db.get(con, item_id) is None


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


def test_clean_links_and_text():
    from clipio.core import clean
    assert clean.clean_url("https://a.com/p?utm_source=x&id=3&fbclid=y") == "https://a.com/p?id=3"
    assert clean.clean_url("https://a.com/p?id=3") == "https://a.com/p?id=3"
    assert clean.clean_text("  hi   there  \n\n\n\nbye ") == "hi there\n\nbye"
    assert clean.join_lines("one\ntwo\n\nthree") == "one two\n\nthree"


def test_copied_link_is_cleaned(con):
    i = add_text(con, "https://shop.com/x?utm_medium=mail&q=1")
    assert db.get(con, i)["text"] == "https://shop.com/x?q=1"


@pytest.mark.parametrize("name,src,out", [
    ("upper", "abc", "ABC"),
    ("json_pretty", '{"a":1}', '{\n  "a": 1\n}'),
    ("base64_encode", "hi", "aGk="),
    ("base64_decode", "aGk=", "hi"),
    ("hex_to_rgb", "#ff0000", "rgb(255, 0, 0)"),
    ("rgb_to_hex", "rgb(0, 128, 255)", "#0080FF"),
    ("json_pretty", "not json", None),
])
def test_transforms(name, src, out):
    from clipio.core import transform
    assert transform.apply(name, src) == out


@pytest.mark.parametrize("text,secret", [
    ("4111 1111 1111 1111", True),
    ("ghp_" + "a1B2" * 9, True),
    ("Kx9#mQ2!vL7p", True),
    ("hello world", False),
    ("1234 5678", False),
])
def test_sensitive(text, secret):
    from clipio.core import sensitive
    assert sensitive.is_sensitive(text) is secret


def test_secrets_expire_and_password_managers_skipped(con):
    i = add_text(con, "4111 1111 1111 1111")
    assert db.get(con, i)["secret"] == 1
    con.execute("UPDATE items SET created=created-3600 WHERE id=?", (i,))
    maintenance.run(con)
    assert db.get(con, i) is None
    assert add_text(con, "pw", source="org.keepassxc.KeePassXC") is None


def test_templates_tags_and_convert(con, fake_clipboard):
    from clipio.core import template
    assert template.expand("{year}!", now=0) == time.strftime("%Y", time.localtime(0)) + "!"
    i = add_text(con, "Hi {clipboard}")
    db.set_tag(con, i, "Mail")
    assert db.get(con, i)["pinned"] == 1 and db.tags(con) == ["Mail"]
    fake_clipboard.write_text("Ada")
    actions.copy(con, fake_clipboard, i)
    assert fake_clipboard.text == "Hi Ada"
    j = add_text(con, "abc")
    new = actions.convert(con, j, "upper")
    assert db.get(con, new)["text"] == "ABC"
    assert "upper" in actions.conversions(con, j)


def test_ignore_app_setting():
    actions.ignore_app("Telegram")
    assert config.load()["ignore_apps"] == ["Telegram"]
    actions.unignore_app("telegram")
    assert config.load()["ignore_apps"] == []
    actions.set_switch("link_titles", True)
    assert config.load()["link_titles"] is True


def test_code_highlight_escapes_html():
    from clipio.core import highlight
    out = highlight.to_rich("if a < b: return '<x>'")
    assert "&lt;x&gt;" in out and "<font" in out and "<x>" not in out


def test_shortcuts_and_features_are_saved(con):
    assert actions.set_shortcut("edit", "Ctrl+Shift+E")
    assert config.load()["key_edit"] == "Ctrl+Shift+E"
    assert not actions.set_shortcut("nope", "X")
    actions.reset_shortcuts()
    assert config.load()["key_edit"] == "Ctrl+E"
    actions.set_switch("detect_secrets", False)
    assert add_text(con, "4111 1111 1111 1111") and db.latest(con)["secret"] == 0
    state = export.build_state(con)
    assert state["shortcuts"]["paste"] == "Return" and state["features"]["detect_secrets"] is False


def test_panel_keep_minutes_setting():
    assert config.load()["panel_keep_minutes"] == 5
    assert actions.set_panel_keep(99999) == 1440
    assert config.load()["panel_keep_minutes"] == 1440
    actions.set_panel_keep(-3)
    assert config.load()["panel_keep_minutes"] == 0
    assert export.build_state(db.connect())["panel_keep_minutes"] == 0
