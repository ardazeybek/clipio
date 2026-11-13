"""Light syntax coloring for code cards: returns Qt styled text (HTML-escaped) with <font> colored tokens."""
import html
import re

# token kind -> color (warm paper palette)
COLORS = {"kw": "#C0623F", "str": "#6E9A5B", "num": "#B07A2A", "com": "#A39886"}

_KEYWORDS = (
    "def class function const let var import from return public private protected static "
    "fn impl struct enum if else elif for while do switch case break continue try catch except "
    "finally raise throw new async await yield lambda with as in is not and or null None true "
    "false True False self this type interface extends implements package use mod pub match"
).split()

_TOKENS = re.compile(
    r"(?P<com>#[^\n]*|//[^\n]*|/\*.*?\*/)"
    r"|(?P<str>\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'|`[^`]*`)"
    r"|(?P<num>\b\d+(?:\.\d+)?\b)"
    r"|(?P<kw>\b(?:" + "|".join(_KEYWORDS) + r")\b)",
    re.S,
)


# Turn code into rich text: escaped, colored, line breaks kept
def to_rich(code: str) -> str:
    code = code.strip("\n").rstrip()
    out, pos = [], 0
    for m in _TOKENS.finditer(code):
        out.append(html.escape(code[pos:m.start()]))
        out.append(f'<font color="{COLORS[m.lastgroup]}">{html.escape(m.group(0))}</font>')
        pos = m.end()
    out.append(html.escape(code[pos:]))
    return "".join(out).replace("\n", "<br>").replace("  ", "&nbsp; ")
