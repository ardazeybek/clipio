"""Bug-hunt probes for clipio/core: each test attacks one promise of a core function."""
import time

from clipio.core import (actions, classify, clean, config, db, export, ingest, sensitive,
                         template, transform)


# A mixed-case tracker name in the list must still be removed
def test_clean_is_tracker_mixed_case_entry():
    assert clean.clean_url("https://x.com/?a=1&trkCampaign=z") == "https://x.com/?a=1"


# Cleaning must keep the other parameters exactly as written
def test_clean_url_keeps_other_params_verbatim():
    url = "https://x.com/p?flag&ids=1,2&q=a%20b&utm_source=y"
    assert clean.clean_url(url) == "https://x.com/p?flag&ids=1,2&q=a%20b"


# Cleaning is idempotent and leaves tracker-free links alone
def test_clean_url_idempotent():
    for url in ("https://a.b/?utm_x=1", "https://a.b/?a=1&fbclid=2#f", "https://a.b/"):
        once = clean.clean_url(url)
        assert clean.clean_url(once) == once


# Copies saved inside Clipio respect the detect_secrets switch
def test_actions_save_text_respects_detect_secrets(con):
    config.set_value("detect_secrets", False)
    item = actions.save_text(con, "ghp_" + "a" * 36)
    assert db.get(con, item)["secret"] == 0


# Re-copying the same text refreshes its order but keeps pin and folder
def test_db_upsert_keeps_pin_and_tag(con):
    i = db.upsert(con, kind="text", hash="h", text="x", source="a")
    db.set_tag(con, i, "work")
    db.upsert(con, kind="text", hash="h", text="x", source="b")
    r = db.get(con, i)
    assert (r["pinned"], r["tag"], r["source"]) == (1, "work", "b")


# Taking an item out of its folder keeps the pin
def test_db_set_tag_empty_keeps_pin(con):
    i = db.upsert(con, kind="text", hash="h", text="x")
    db.set_tag(con, i, "f")
    db.set_tag(con, i, "")
    assert db.get(con, i)["pinned"] == 1 and db.tags(con) == []


# Trimming keeps the newest unpinned items and every pinned one
def test_db_trim_count_keeps_newest(con):
    ids = []
    for n in range(5):
        ids.append(db.upsert(con, kind="text", hash=str(n), text=str(n)))
        con.execute("UPDATE items SET used=? WHERE id=?", (n, ids[-1]))
    db.set_pinned(con, ids[0], True)
    db.trim_count(con, 2)
    assert {r["id"] for r in db.list_items(con)} == {ids[0], ids[3], ids[4]}


# Image trimming drops the oldest first
def test_db_trim_image_bytes_oldest_first(con):
    for n in range(3):
        i = db.upsert(con, kind="image", hash=str(n), image_file=f"{n}.png", size=10)
        con.execute("UPDATE items SET used=? WHERE id=?", (n, i))
    db.trim_image_bytes(con, 20)
    assert sorted(r["image_file"] for r in db.list_items(con)) == ["1.png", "2.png"]


# Panel listing and image lookups use indexes, not full scans
def test_db_indexes_used(con):
    plan = " ".join(r[3] for r in con.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM items ORDER BY pinned DESC, used DESC LIMIT 300"))
    assert "TEMP B-TREE" not in plan
    plan = " ".join(r[3] for r in con.execute(
        "EXPLAIN QUERY PLAN SELECT 1 FROM items WHERE image_file='x'"))
    assert "INDEX" in plan


# Same link with and without trackers is stored once
def test_ingest_capture_dedupes_cleaned_links(con):
    cfg = config.load()
    a = ingest.capture(con, ingest.Snapshot(text=b"https://x.com/?a=1&utm_source=z"), "", cfg)
    b = ingest.capture(con, ingest.Snapshot(text=b"https://x.com/?a=1"), "", cfg)
    assert a == b


# Empty, blank and oversized copies are not saved
def test_ingest_capture_edges(con):
    cfg = config.load()
    assert ingest.capture(con, ingest.Snapshot(text=b"   "), "", cfg) is None
    assert ingest.capture(con, ingest.Snapshot(text=b"a" * (cfg["max_text_kb"] * 1024 + 1)), "", cfg) is None
    assert ingest.capture(con, ingest.Snapshot(text=b"x"), "KeePassXC", cfg) is None


# Classification of common single-line kinds
def test_classify_kinds():
    assert classify.classify("#ff8800") == ("color", "#ff8800")
    assert classify.classify("www.example.com/a") == ("url", "example.com")
    assert classify.classify("a@b.co") == ("email", "b.co")
    assert classify.classify("") == ("text", "")


# Unknown or uppercase-free placeholders behave
def test_template_expand():
    assert template.expand("{year}-{clipboard}", "c", now=0).endswith("-c")
    assert template.expand("{nope}") == "{nope}"
    assert not template.has_placeholders("")


# Conversions round trip and refuse no-ops
def test_transform_roundtrip():
    assert transform.apply("rgb_to_hex", transform.apply("hex_to_rgb", "#abc")) == "#AABBCC"
    assert transform.apply("base64_decode", transform.apply("base64_encode", "hé")) == "hé"
    assert transform.apply("upper", "ABC") is None
    assert transform.apply("missing", "x") is None


# Secrets are spotted; ordinary sentences are not
def test_sensitive_basic():
    assert sensitive.is_sensitive("4111 1111 1111 1111")
    assert not sensitive.is_sensitive("hello world, see you at 10")
    assert not sensitive.is_sensitive("")


# Wrong types and out-of-range values fall back or clamp
def test_config_validated(tmp_path):
    config.write_default_if_missing()
    config.set_value("retention_days", 0)
    config.set_value("hotkey", 'a"b\\c')
    cfg = config.load()
    assert cfg["retention_days"] == 1 and cfg["hotkey"] == 'a"b\\c'


# Export of an empty text item and a code card
def test_export_item_lines(con):
    i = db.upsert(con, kind="text", hash="h", text="", hint="code")
    d = export.item(db.get(con, i))
    assert d["lines"] == 0 and d["rich"] == ""
    assert export.build_state(con)["total"] == 1


# Secrets expire by creation time
def test_db_purge_secrets(con):
    i = db.upsert(con, kind="text", hash="h", text="x", secret=1)
    con.execute("UPDATE items SET created=? WHERE id=?", (time.time() - 3600, i))
    assert db.purge_secrets(con, 5) == 1
