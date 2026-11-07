"""The `clipio` command for everything that does not need a running app."""
import json

from clipio import __version__, cli
from clipio.core import config, db, ingest
from clipio.core.ingest import Snapshot


# Add one text item straight into the database
def add(text):
    con = db.connect()
    ingest.capture(con, Snapshot(formats=["text/plain"], text=text.encode()), "", config.load())
    con.close()


def test_help_and_version(capsys):
    assert cli.main([]) == 0
    assert "usage: clipio" in capsys.readouterr().out
    assert cli.main(["version"]) == 0
    assert capsys.readouterr().out.strip() == __version__


def test_list_pin_delete_clear(capsys):
    add("one")
    add("two")
    assert cli.main(["list"]) == 0
    rows = [json.loads(l) for l in capsys.readouterr().out.splitlines()]
    assert {r["text"] for r in rows} == {"one", "two"}
    first = rows[0]["id"]
    assert cli.main(["pin", str(first)]) == 0
    assert cli.main(["clear"]) == 0
    capsys.readouterr()
    cli.main(["list"])
    left = [json.loads(l) for l in capsys.readouterr().out.splitlines()]
    assert [r["id"] for r in left] == [first] and left[0]["pinned"]
    assert cli.main(["delete", str(first)]) == 0


def test_pause_retention_status(capsys):
    assert cli.main(["pause"]) == 0
    assert cli.main(["retention", "5"]) == 0
    capsys.readouterr()
    assert cli.main(["status"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["paused"] and status["retention_days"] == 5 and status["running"] is False
    assert cli.main(["resume"]) == 0


def test_bad_usage_returns_errors():
    assert cli.main(["pin"]) == 2
    assert cli.main(["retention", "abc"]) == 2
    assert cli.main(["paste", "x"]) == 2
    assert cli.main(["autostart", "maybe"]) == 2
    assert cli.main(["no-such-command"]) == 2
