"""Fills placeholders like {date}, {time} and {clipboard} in pinned snippets when they are pasted."""
import re
import time

# placeholder -> strftime format
_FORMATS = {"date": "%d.%m.%Y", "time": "%H:%M", "datetime": "%d.%m.%Y %H:%M",
            "year": "%Y", "weekday": "%A", "iso": "%Y-%m-%d"}
_TOKEN = re.compile(r"\{(date|time|datetime|year|weekday|iso|clipboard)\}")


# True when the text has at least one known placeholder
def has_placeholders(text: str) -> bool:
    return bool(text and _TOKEN.search(text))


# Replace the placeholders; `clipboard` is the text that was on the clipboard before
def expand(text: str, clipboard: str = "", now: float | None = None) -> str:
    t = time.localtime(now)

    # value for one placeholder
    def value(m: re.Match) -> str:
        key = m.group(1)
        return clipboard if key == "clipboard" else time.strftime(_FORMATS[key], t)

    return _TOKEN.sub(value, text)
