"""Draws every README picture in docs/assets/art/ in Clipio's paper theme (run: python docs/assets/art/make_art.py).

Each picture is plain SVG built from the same pieces: a note card on a paper stack, tape,
small drawn icons (ICONS) and text. Change a color or an icon here and run it again.
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent
FONT = "Nunito, 'Segoe UI', -apple-system, 'Helvetica Neue', Arial, sans-serif"

# paper theme (same values as clipio/ui/components/Theme.qml)
PAPER, SHEET, EDGE, STACK = "#F6EFE1", "#FFFCF5", "#E4D8C2", "#E9DFCB"
INK, PENCIL, ACCENT, TAPE, SAGE = "#3D3530", "#9A8E7E", "#E58F6F", "#F3D9A4", "#9CC3A6"
DOTS, DARK_ACCENT, BEAK = "#C9BBA4", "#C97556", "#F2B661"


# ---------- small building blocks ----------

# Text in the README font
def text(x, y, s, size: float = 14, weight=800, fill=INK, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}">{s}</text>')


# A note card lying on a paper stack
def card(x, y, w, h, r=14, fill=SHEET):
    return (f'<rect x="{x + 5}" y="{y + 5}" width="{w}" height="{h}" rx="{r}" fill="{STACK}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{EDGE}" stroke-width="2"/>')


# A strip of tape, centered on (cx, cy)
def tape(cx, cy, w=46, color=TAPE, tilt=-3):
    return (f'<rect x="{cx - w / 2}" y="{cy - 8}" width="{w}" height="16" rx="2" fill="{color}" opacity="0.92" '
            f'transform="rotate({tilt} {cx} {cy})"/>')


# A key cap with a label
def key(x, y, label, w=None, solid=False):
    w = w or max(22, 10 + 7 * len(label))
    fill, stroke, ink = (ACCENT, ACCENT, SHEET) if solid else (SHEET, DOTS, INK)
    return (f'<rect x="{x}" y="{y}" width="{w}" height="18" rx="5" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            + text(x + w / 2, y + 13, label, 11, 800, ink, "middle"))


# A numbered peach dot
def badge(cx, cy, n):
    return f'<circle cx="{cx}" cy="{cy}" r="13" fill="{ACCENT}"/>' + text(cx, cy + 5, n, 13, 800, SHEET, "middle")


# Dotted pencil arrow from (x1, y) to (x2, y), curving up; the head follows the curve's end
def arrow(x1, x2, y):
    mid = (x1 + x2) / 2
    return (f'<path d="M{x1} {y} Q{mid} {y - 22} {x2} {y}" fill="none" stroke="{DOTS}" stroke-width="2.4" '
            f'stroke-linecap="round" stroke-dasharray="1 7" marker-end="url(#head)"/>')


# Arrow head that turns with the line it ends (used by arrow())
ARROW_DEFS = (f'<marker id="head" viewBox="0 0 10 10" refX="1.5" refY="5" markerWidth="7" markerHeight="7" '
              f'markerUnits="userSpaceOnUse" orient="auto"><path d="M1 1 L8 5 L1 9" fill="none" stroke="{DOTS}" '
              f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></marker>')


# Wrap drawn parts into an SVG document
def svg(w, h, body, comment, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
            f'  <!-- {comment} (drawn by make_art.py) -->\n'
            + (f"  <defs>{defs}</defs>\n" if defs else "") + f"  {body}\n</svg>\n")


# ---------- icons (about 40 px, centered on 0,0) ----------

def _stroke(paths, color, width=3.2):
    return (f'<g fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">'
            + "".join(f'<path d="{d}"/>' for d in paths) + "</g>")


ICONS = {
    # why Clipio
    "key": f'<rect x="-17" y="-15" width="34" height="32" rx="8" fill="{STACK}"/><rect x="-17" y="-18" width="34" height="31" rx="8" fill="{SHEET}" stroke="{DOTS}" stroke-width="2"/>' + text(0, 3, "V", 16, 800, ACCENT, "middle"),
    "paper": f'<rect x="-16" y="-15" width="24" height="30" rx="5" fill="{SAGE}" transform="rotate(-10)"/><rect x="-9" y="-14" width="24" height="30" rx="5" fill="{SHEET}" stroke="{EDGE}" stroke-width="2" transform="rotate(6)"/><rect x="-12" y="-20" width="16" height="7" rx="1.5" fill="{TAPE}" transform="rotate(-14)"/><rect x="-3" y="-4" width="13" height="3" rx="1.5" fill="{EDGE}" transform="rotate(6)"/><rect x="-3" y="3" width="13" height="3" rx="1.5" fill="{EDGE}" transform="rotate(6)"/>',
    "lock": f'<path d="M-8 -4 v-6 a8 8 0 0 1 16 0 v6" fill="none" stroke="{PENCIL}" stroke-width="3.5" stroke-linecap="round"/><rect x="-13" y="-5" width="26" height="21" rx="6" fill="{ACCENT}"/><circle cx="0" cy="4" r="3" fill="{SHEET}"/><rect x="-1.2" y="5" width="2.4" height="6" rx="1.2" fill="{SHEET}"/>',
    "feather": f'<path d="M12 -16 c-14 2 -24 12 -24 28 c14 0 24 -10 24 -28 z" fill="{SAGE}"/><path d="M10 -13 L-14 15" stroke="#5E8C6A" stroke-width="2" stroke-linecap="round"/><path d="M-2 -2 h8 M-7 4 h8" stroke="{SHEET}" stroke-width="1.6" stroke-linecap="round"/>',
    "update": _stroke(["M-12 -3 a12 12 0 0 1 21 -6", "M10 -15 v7 h-7", "M12 3 a12 12 0 0 1 -21 6", "M-10 15 v-7 h7"], ACCENT, 3.4),
    "devices": f'<rect x="-19" y="-13" width="26" height="18" rx="3" fill="{SHEET}" stroke="{PENCIL}" stroke-width="2"/><rect x="-14" y="8" width="16" height="3" rx="1.5" fill="{PENCIL}"/><rect x="2" y="-4" width="18" height="13" rx="3" fill="{TAPE}" stroke="#C9A35E" stroke-width="2"/><rect x="11" y="-16" width="10" height="16" rx="2.5" fill="{SAGE}" stroke="#6E9C7A" stroke-width="2"/>',
    # everyday
    "paste": f'<rect x="-14" y="-15" width="20" height="24" rx="4" fill="{SHEET}" stroke="{EDGE}" stroke-width="2"/><rect x="-10" y="-9" width="12" height="3" rx="1.5" fill="{DOTS}"/><rect x="-10" y="-3" width="9" height="3" rx="1.5" fill="{DOTS}"/>' + _stroke(["M4 4 h11", "M10 -2 l5 6 l-5 6"], ACCENT, 3),
    "search": _stroke(["M5.5 5.5 L13 13"], ACCENT, 4) + f'<circle cx="-3" cy="-3" r="10" fill="{SHEET}" stroke="{ACCENT}" stroke-width="3.4"/>',
    "pin": f'<path d="M-6 -15 h12 l-2 9 l6 6 h-20 l6 -6 z" fill="{SAGE}"/><path d="M0 0 v14" stroke="{PENCIL}" stroke-width="3" stroke-linecap="round"/>',
    "number": f'<rect x="-18" y="-11" width="17" height="22" rx="5" fill="{SHEET}" stroke="{DOTS}" stroke-width="2"/>' + text(-9.5, 5, "Alt", 7.5, 800, INK, "middle") + f'<rect x="2" y="-11" width="16" height="22" rx="5" fill="{ACCENT}"/>' + text(10, 5, "1", 12, 800, SHEET, "middle"),
    "queue": "".join(f'<rect x="{-14 + 4 * i}" y="{-14 + 7 * i}" width="22" height="12" rx="3" fill="{SHEET}" stroke="{EDGE if i < 2 else ACCENT}" stroke-width="2"/>' for i in range(3)),
    # smart cards
    "color": f'<circle cx="-6" cy="-5" r="9" fill="{ACCENT}"/><circle cx="7" cy="-3" r="9" fill="{SAGE}" opacity="0.9"/><circle cx="0" cy="8" r="9" fill="{TAPE}" opacity="0.9"/>',
    "code": _stroke(["M-8 -9 l-8 9 l8 9", "M8 -9 l8 9 l-8 9"], ACCENT, 3.4) + _stroke(["M3 -12 l-6 24"], SAGE, 3),
    "link": _stroke(["M-2 4 l6 -6", "M-1 -7 l3 -3 a6 6 0 0 1 8.5 8.5 l-3 3", "M1 7 l-3 3 a6 6 0 0 1 -8.5 -8.5 l3 -3"], ACCENT, 3.4),
    "image": f'<rect x="-16" y="-13" width="32" height="26" rx="5" fill="{SHEET}" stroke="{EDGE}" stroke-width="2"/><circle cx="-6" cy="-4" r="3.5" fill="{TAPE}"/><path d="M-14 11 l9 -9 l6 6 l4 -4 l9 7 z" fill="{SAGE}"/>',
    "app": f'<rect x="-16" y="-12" width="32" height="24" rx="5" fill="{SHEET}" stroke="{EDGE}" stroke-width="2"/><rect x="-16" y="-12" width="32" height="7" rx="3" fill="{STACK}"/><circle cx="-11" cy="-8.5" r="1.6" fill="{ACCENT}"/><circle cx="-6" cy="-8.5" r="1.6" fill="{TAPE}"/>' + text(0, 8, "@app", 8.5, 800, ACCENT, "middle"),
    "edit": f'<path d="M-12 12 l2 -8 l15 -15 l6 6 l-15 15 z" fill="{TAPE}" stroke="#C9A35E" stroke-width="1.8" stroke-linejoin="round"/><path d="M-12 12 l2 -8 l6 6 z" fill="{INK}"/><path d="M3 -9 l6 6" stroke="#C9A35E" stroke-width="1.8"/>',
    "template": text(0, 5, "{ }", 18, 800, ACCENT, "middle"),
    # privacy
    "hide": f'<path d="M-16 0 q16 -16 32 0 q-16 16 -32 0 z" fill="{SHEET}" stroke="{PENCIL}" stroke-width="2.4"/><circle cx="0" cy="0" r="5" fill="{PENCIL}"/>' + _stroke(["M-13 -11 L13 11"], ACCENT, 3.2),
    "block": f'<circle cx="0" cy="0" r="13" fill="none" stroke="{ACCENT}" stroke-width="3.4"/>' + _stroke(["M-9 9 L9 -9"], ACCENT, 3.4),
    "pause": f'<rect x="-9" y="-12" width="6" height="24" rx="3" fill="{ACCENT}"/><rect x="3" y="-12" width="6" height="24" rx="3" fill="{ACCENT}"/>',
    "broom": f'<path d="M8 -15 L-2 4" stroke="{PENCIL}" stroke-width="3" stroke-linecap="round"/><path d="M-7 1 l9 5 l-4 9 q-9 -2 -12 -8 z" fill="{TAPE}" stroke="#C9A35E" stroke-width="1.6" stroke-linejoin="round"/>',
    "home": f'<path d="M-14 0 L0 -13 L14 0" fill="none" stroke="{ACCENT}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/><rect x="-10" y="-2" width="20" height="15" rx="3" fill="{SHEET}" stroke="{EDGE}" stroke-width="2"/><rect x="-3" y="4" width="6" height="9" rx="1.5" fill="{SAGE}"/>',
    # settings tabs
    "guide": f'<path d="M0 -10 q-8 -5 -16 -3 v22 q8 -2 16 3 z" fill="{SHEET}" stroke="{EDGE}" stroke-width="2"/><path d="M0 -10 q8 -5 16 -3 v22 q-8 -2 -16 3 z" fill="{SAGE}" opacity="0.85"/>',
    "keyboard": f'<rect x="-17" y="-10" width="34" height="21" rx="5" fill="{SHEET}" stroke="{DOTS}" stroke-width="2"/>' + "".join(f'<rect x="{-13 + 7 * c}" y="{-6 + 6 * r}" width="5" height="4" rx="1.2" fill="{DOTS}"/>' for r in range(2) for c in range(4)) + f'<rect x="-9" y="5" width="18" height="3.5" rx="1.5" fill="{ACCENT}"/>',
    "toggles": f'<rect x="-16" y="-12" width="26" height="10" rx="5" fill="{SAGE}"/><circle cx="5" cy="-7" r="4" fill="{SHEET}"/><rect x="-10" y="3" width="26" height="10" rx="5" fill="{EDGE}"/><circle cx="-5" cy="8" r="4" fill="{SHEET}"/>',
    "storage": f'<rect x="-14" y="-8" width="28" height="20" rx="4" fill="{TAPE}" stroke="#C9A35E" stroke-width="2"/><rect x="-16" y="-14" width="32" height="8" rx="3" fill="{SHEET}" stroke="#C9A35E" stroke-width="2"/><rect x="-5" y="-1" width="10" height="3" rx="1.5" fill="#C9A35E"/>',
    # support
    "bug": f'<ellipse cx="0" cy="3" rx="9" ry="11" fill="{ACCENT}"/><circle cx="0" cy="-9" r="5" fill="{INK}"/>' + _stroke(["M-9 0 h-6", "M9 0 h6", "M-8 8 l-6 4", "M8 8 l6 4", "M-3 -13 l-3 -4", "M3 -13 l3 -4"], INK, 2) + f'<path d="M0 -8 v22" stroke="{DARK_ACCENT}" stroke-width="1.6"/>',
    "chat": f'<path d="M-16 -12 h20 a4 4 0 0 1 4 4 v9 a4 4 0 0 1 -4 4 h-11 l-6 5 v-5 h-3 a4 4 0 0 1 -4 -4 v-9 a4 4 0 0 1 4 -4 z" fill="{SAGE}"/><path d="M2 -4 h12 a4 4 0 0 1 4 4 v8 a4 4 0 0 1 -4 4 h-1 v4 l-5 -4 h-6 a4 4 0 0 1 -4 -4 v-8 a4 4 0 0 1 4 -4 z" fill="{TAPE}" stroke="{SHEET}" stroke-width="2"/>',
    "mail": f'<rect x="-16" y="-11" width="32" height="22" rx="4" fill="{SHEET}" stroke="{EDGE}" stroke-width="2"/>' + _stroke(["M-14 -8 L0 3 L14 -8"], ACCENT, 2.8),
}


# The Windows 11 mark: four flat panes in Windows blue
def windows_icon():
    panes = "".join(f'<rect x="{x}" y="{y}" width="19.5" height="19.5" rx="2" fill="url(#win)"/>'
                    for x in (-21, 1.5) for y in (-21, 1.5))
    return panes


WIN_DEFS = ('<linearGradient id="win" gradientUnits="userSpaceOnUse" x1="-21" y1="-21" x2="21" y2="21">'
            '<stop offset="0" stop-color="#3CCBF4"/><stop offset="0.55" stop-color="#1A8FE3"/>'
            '<stop offset="1" stop-color="#0063B1"/></linearGradient>')


# The command key: a small square with a loop at each corner
def mac_icon():
    return _stroke(["M-7 -7 h14 v14 h-14 z", "M-7 -7 v-6 a6 6 0 1 0 -6 6 z", "M7 -7 v-6 a6 6 0 1 1 6 6 z",
                    "M-7 7 v6 a6 6 0 1 1 -6 -6 z", "M7 7 v6 a6 6 0 1 0 6 -6 z"], INK, 4.2)


# A round, friendly penguin with short flippers, rosy cheeks and shiny eyes
def penguin_icon():
    return (
        f'<ellipse cx="-14.5" cy="6" rx="4.2" ry="7.5" fill="{INK}" transform="rotate(22 -14.5 6)"/>'
        f'<ellipse cx="14.5" cy="6" rx="4.2" ry="7.5" fill="{INK}" transform="rotate(-22 14.5 6)"/>'
        f'<ellipse cx="0" cy="2" rx="16" ry="19" fill="{INK}"/>'
        f'<ellipse cx="0" cy="8" rx="11" ry="12.5" fill="{SHEET}"/>'
        f'<circle cx="-5.2" cy="-5" r="6.6" fill="{SHEET}"/><circle cx="5.2" cy="-5" r="6.6" fill="{SHEET}"/>'
        f'<circle cx="-5" cy="-5" r="2.9" fill="{INK}"/><circle cx="5" cy="-5" r="2.9" fill="{INK}"/>'
        f'<circle cx="-4" cy="-6.1" r="1.1" fill="{SHEET}"/><circle cx="6" cy="-6.1" r="1.1" fill="{SHEET}"/>'
        f'<ellipse cx="-9.5" cy="1.5" rx="2.6" ry="1.7" fill="{ACCENT}" opacity="0.55"/>'
        f'<ellipse cx="9.5" cy="1.5" rx="2.6" ry="1.7" fill="{ACCENT}" opacity="0.55"/>'
        f'<path d="M-3.4 -0.5 q3.4 -1.6 6.8 0 q-3.4 4.6 -6.8 0 z" fill="{BEAK}"/>'
        f'<ellipse cx="-6.5" cy="21" rx="5.5" ry="2.8" fill="{BEAK}"/><ellipse cx="6.5" cy="21" rx="5.5" ry="2.8" fill="{BEAK}"/>'
        f'<path d="M-2 -16.5 q2 -4 4.5 -2.5" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>'
    )


# ---------- pictures ----------

# Download card of one system (a note on a stack, with tape, icon, name and a download pill)
def os_card(title, sub, pill, icon, tape_color, tilt, defs=""):
    w_pill = round(30 + len(pill) * 6.0)
    x_pill = 106 - w_pill / 2
    ix = x_pill + 13
    body = (card(6, 10, 200, 144, 16) + tape(107, 10, 46, tape_color, tilt)
            + f'<g transform="translate(106 54)">{icon}</g>'
            + text(106, 104, title, 17, 800, INK, "middle") + text(106, 121, sub, 11.5, 600, PENCIL, "middle")
            + f'<rect x="{x_pill:g}" y="130" width="{w_pill}" height="16" rx="8" fill="{ACCENT}"/>'
            + _stroke([f"M{ix:g} 134 v6", f"M{ix - 2.5:g} 137.5 l2.5 2.5 l2.5 -2.5", f"M{ix - 4:g} 142 h8"], SHEET, 1.6)
            + text(x_pill + 22, 141.5, pill, 9.5, 800, SHEET))
    return svg(220, 168, body, f"{title} download card", defs)


# Row of small cards: icon in a paper dot, title and one line below (cols per row)
def tiles(items, cols=3, w=244, h=74, gap=14, comment="tiles"):
    rows = (len(items) + cols - 1) // cols
    parts = []
    for i, (ic, title, sub) in enumerate(items):
        x, y = (i % cols) * (w + gap), (i // cols) * (h + gap) + 2
        parts.append(f'<g transform="translate({x} {y})">' + card(0, 0, w, h)
                     + f'<circle cx="38" cy="{h / 2}" r="25" fill="{PAPER}"/>'
                     + f'<g transform="translate(38 {h / 2})">{ICONS[ic]}</g>'
                     + text(74, h / 2 - 3, title, 15) + text(74, h / 2 + 15, sub, 11.5, 600, PENCIL) + "</g>")
    return svg(cols * w + (cols - 1) * gap + 8, rows * h + (rows - 1) * gap + 10, "".join(parts), comment)


# A feature group: tape label on a paper sheet, items in two columns with icons
def feature_group(name, color, items, comment):
    w, row = 760, 58
    rows = (len(items) + 1) // 2
    h = 46 + rows * row + 10
    parts = [card(0, 10, w - 8, h - 14, 18, PAPER), tape(80, 12, 120, color, -2), text(80, 17, name, 13, 800, INK, "middle")]
    for i, (ic, title, sub) in enumerate(items):
        x, y = 20 + (i % 2) * 366, 42 + (i // 2) * row
        parts.append(f'<g transform="translate({x} {y})">' + card(0, 0, 344, 48, 12)
                     + f'<g transform="translate(26 24) scale(0.78)">{ICONS[ic]}</g>'
                     + text(52, 21, title, 13.5) + text(52, 37, sub, 11, 600, PENCIL) + "</g>")
    return svg(w, h, "".join(parts), comment)


# Copy → shortcut → pasted
def steps():
    p = [card(0, 8, 752, 190, 20, PAPER), tape(376, 9, 72),
         arrow(226, 280, 92), arrow(478, 532, 92)]
    # 1 copy
    p.append('<g transform="translate(46 34)">' + card(0, 0, 150, 96, 12)
             + f'<rect x="16" y="20" width="92" height="7" rx="3.5" fill="{EDGE}"/><rect x="14" y="36" width="104" height="13" rx="4" fill="{TAPE}" opacity="0.8"/>'
             + f'<rect x="18" y="39" width="88" height="7" rx="3.5" fill="#B9A98F"/><rect x="16" y="58" width="70" height="7" rx="3.5" fill="{EDGE}"/>'
             + key(40, 72, "Ctrl", 34) + key(80, 72, "C") + "</g>")
    p += [badge(46, 34, "1"), text(121, 160, "Copy as usual", 16, 800, INK, "middle"),
          text(121, 178, "Clipio keeps every copy", 12, 600, PENCIL, "middle")]
    # 2 the panel
    p.append('<g transform="translate(300 28)">' + card(0, 0, 152, 90, 14, PAPER)
             + f'<rect x="12" y="11" width="128" height="16" rx="8" fill="{SHEET}" stroke="{ACCENT}" stroke-width="1.5"/><circle cx="23" cy="19" r="3.5" fill="none" stroke="{ACCENT}" stroke-width="1.5"/>'
             + f'<rect x="12" y="35" width="128" height="22" rx="7" fill="{SHEET}" stroke="{ACCENT}" stroke-width="2"/><rect x="20" y="43" width="74" height="6" rx="3" fill="#B9A98F"/>'
             + f'<rect x="12" y="62" width="128" height="18" rx="7" fill="{SHEET}" stroke="{EDGE}" stroke-width="1.5"/><rect x="20" y="68" width="22" height="7" rx="2" fill="{SAGE}"/><rect x="48" y="69" width="54" height="5" rx="2.5" fill="{EDGE}"/>'
             + "</g>")
    p += [key(316, 128, "Ctrl", 34), key(356, 128, "Shift", 40), key(402, 128, "V", 34, True),
          badge(300, 28, "2"), text(376, 170, "Press the shortcut", 16, 800, INK, "middle"),
          text(376, 187, "Search or pick a card", 12, 600, PENCIL, "middle")]
    # 3 pasted
    p.append('<g transform="translate(552 34)">' + card(0, 0, 150, 96, 12)
             + f'<path d="M0 12 a12 12 0 0 1 12 -12 h126 a12 12 0 0 1 12 12 v8 h-150 z" fill="{PAPER}"/>'
             + f'<circle cx="14" cy="10" r="3.5" fill="{ACCENT}"/><circle cx="26" cy="10" r="3.5" fill="{TAPE}"/><circle cx="38" cy="10" r="3.5" fill="{SAGE}"/>'
             + f'<rect x="14" y="32" width="84" height="7" rx="3.5" fill="#B9A98F"/><rect x="99" y="29" width="2" height="13" rx="1" fill="{ACCENT}"/>'
             + f'<rect x="14" y="50" width="110" height="6" rx="3" fill="{EDGE}"/><rect x="14" y="62" width="76" height="6" rx="3" fill="{EDGE}"/>'
             + f'<circle cx="124" cy="74" r="14" fill="{SAGE}"/>' + _stroke(["M117 74 l5 5 l9 -10"], SHEET, 3) + "</g>")
    p += [badge(552, 34, "3"), text(627, 160, "It's pasted", 16, 800, INK, "middle"),
          text(627, 178, "Right where you were typing", 12, 600, PENCIL, "middle")]
    return svg(760, 210, "".join(p), "How Clipio works: copy, press the shortcut, it is pasted", ARROW_DEFS)


# Download → open and press Install → done
def install_steps():
    p = [card(0, 8, 752, 190, 20, PAPER), tape(376, 9, 72, SAGE, 2),
         arrow(226, 280, 92), arrow(478, 532, 92)]
    # 1 the download button
    p.append('<g transform="translate(46 62)">'
             + f'<rect x="0" y="6" width="150" height="40" rx="12" fill="{DARK_ACCENT}"/><rect x="0" y="2" width="150" height="40" rx="12" fill="{ACCENT}"/>'
             + _stroke(["M24 12 v12", "M19 19.5 l5 5 l5 -5", "M16 26 v3 a2 2 0 0 0 2 2 h12 a2 2 0 0 0 2 -2 v-3"], SHEET, 2.4)
             + text(88, 27, "Download", 14, 800, SHEET, "middle") + "</g>")
    p += [badge(46, 62, "1"), text(121, 160, "Download", 16, 800, INK, "middle"),
          text(121, 178, "The page picks your system", 12, 600, PENCIL, "middle")]
    # 2 the setup window
    p.append('<g transform="translate(300 30)">' + card(0, 0, 152, 106, 14, PAPER)
             + f'<g transform="translate(76 36)">' + ICONS["paper"] + "</g>"
             + text(76, 70, "Install Clipio", 11.5, 800, INK, "middle")
             + f'<rect x="46" y="78" width="60" height="18" rx="6" fill="{ACCENT}"/>' + text(76, 91, "Install", 10.5, 800, SHEET, "middle")
             + "</g>")
    p += [badge(300, 30, "2"), text(376, 164, "Press Install", 16, 800, INK, "middle"),
          text(376, 182, "No Python, no admin rights", 12, 600, PENCIL, "middle")]
    # 3 ready
    p.append('<g transform="translate(552 34)">' + card(0, 0, 150, 96, 12)
             + f'<circle cx="75" cy="40" r="22" fill="{SAGE}"/>' + _stroke(["M64 40 l8 8 l14 -16"], SHEET, 4)
             + text(75, 82, "Clipio is ready!", 11.5, 800, INK, "middle") + "</g>"
             + "".join(f'<rect x="{x}" y="{y}" width="7" height="4" rx="1" fill="{c}" transform="rotate({r} {x} {y})"/>'
                       for x, y, c, r in [(585, 52, ACCENT, 20), (668, 48, TAPE, -30), (592, 84, SAGE, 50), (676, 86, ACCENT, -15), (628, 40, TAPE, 70)]))
    p += [badge(552, 34, "3"), text(627, 160, "That's it", 16, 800, INK, "middle"),
          text(627, 178, "Starts with your computer", 12, 600, PENCIL, "middle")]
    return svg(760, 210, "".join(p), "Install Clipio in three steps: download, press Install, done", ARROW_DEFS)


# One support card (linked separately in the README)
def support_card(ic, title, sub):
    body = (card(4, 4, 232, 84) + f'<circle cx="44" cy="46" r="25" fill="{PAPER}"/>'
            + f'<g transform="translate(44 46)">{ICONS[ic]}</g>' + text(80, 43, title, 15) + text(80, 61, sub, 11.5, 600, PENCIL))
    return svg(246, 98, body, f"support card: {title}")


# Write every picture
def main() -> None:
    files = {
        "os-windows.svg": os_card("Windows", "Windows 10 · 11", "Download .exe", windows_icon(), TAPE, -4, WIN_DEFS),
        "os-macos.svg": os_card("macOS", "Apple Silicon · Intel", "Download .dmg", mac_icon(), SAGE, 3),
        "os-linux.svg": os_card("Linux", "X11 · Wayland", "Download", penguin_icon(), ACCENT, -2),
        "highlights.svg": tiles([("key", "One shortcut", "Pick a copy, it's pasted"),
                                 ("paper", "Lovely to look at", "Calm paper theme"),
                                 ("lock", "Private", "Stays on your computer"),
                                 ("feather", "Light", "About 25 MB in the background"),
                                 ("update", "Updates itself", "Quietly, while you work"),
                                 ("devices", "Everywhere", "Windows, macOS and Linux")], comment="Why Clipio highlights"),
        "steps.svg": steps(),
        "install.svg": install_steps(),
        "features-everyday.svg": feature_group("Everyday", TAPE, [
            ("paste", "Quick paste", "Enter or a click pastes it where you were"),
            ("search", "Search and tabs", "All, Text, Images and Pinned"),
            ("pin", "Pins and folders", "Pinned items never expire"),
            ("number", "Alt + number", "Alt + 1…9 pastes one of the first nine"),
            ("queue", "Paste queue", "Mark several, paste them one by one")], "Everyday features"),
        "features-smart.svg": feature_group("Smart cards", SAGE, [
            ("color", "Colors", "A swatch plus HEX ↔ RGB"),
            ("code", "Code", "Colored like in your editor"),
            ("link", "Clean links", "Tracking bits removed, page titles"),
            ("image", "Images", "Thumbnails and text from images (OCR)"),
            ("app", "Source app", "Each card shows its app; @app filters"),
            ("edit", "Edit and convert", "Case, JSON, Base64, URL encoding"),
            ("template", "Templates", "{date}, {time}, {clipboard} filled in")], "Smart card features"),
        "features-privacy.svg": feature_group("Privacy", ACCENT, [
            ("hide", "Secrets hide themselves", "Passwords and keys vanish in minutes"),
            ("block", "Ignored apps", "Password managers are always skipped"),
            ("pause", "Pause", "Stop recording with one click"),
            ("broom", "Auto cleanup", "Old items go after 1–30 days"),
            ("home", "Local only", "A small database on your own disk")], "Privacy features"),
        "settings-tabs.svg": tiles([("guide", "How to", "An animated guide per feature"),
                                    ("keyboard", "Shortcuts", "Click a key, press the new one"),
                                    ("toggles", "Features", "Switch each one on or off"),
                                    ("storage", "Storage", "How long items are kept")], cols=2, w=372, comment="Settings tabs"),
        "support-issues.svg": support_card("bug", "Bugs and ideas", "GitHub Issues"),
        "support-discussions.svg": support_card("chat", "Questions", "GitHub Discussions"),
        "support-mail.svg": support_card("mail", "Anything else", "Send an email"),
    }
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
    print(f"wrote {len(files)} pictures to {OUT}")


if __name__ == "__main__":
    main()
