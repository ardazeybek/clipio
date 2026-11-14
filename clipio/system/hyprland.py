"""Hyprland niceties: a runtime window rule so the panel floats, centered, without borders, blur, shadow or inner glow."""
import json
import subprocess

from . import is_hyprland

APP_CLASS = "clipio"

# Lua configs (Hyprland 0.54+)
LUA_RULE = ('hl.window_rule({ name = "clipio-panel", match = { class = "^clipio$" }, float = true, '
            'center = true, opacity = "1.0 override", no_blur = true, no_shadow = true, no_glow = true, '
            'border_size = 0, rounding = 0, no_anim = true })')

# Same rule without no_glow, for Lua Hyprland older than 0.57 (it rejects unknown fields)
LUA_RULE_NO_GLOW = LUA_RULE.replace(" no_glow = true,", "")

# Classic hyprlang configs (older Hyprland)
CLASSIC_RULES = ["float", "center", "opaque", "noblur", "noshadow", "noborder", "noanim", "rounding 0"]


# Run hyprctl; True when it answered "ok"
def _hyprctl(args: list[str]) -> bool:
    try:
        r = subprocess.run(["hyprctl", *args], capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0 and r.stdout.strip().lower().startswith("ok")


# Add the panel's window rule for this session (nothing is written to the user's config)
def apply_window_rule() -> bool:
    if not is_hyprland():
        return False
    # newest rule first, then the pre-0.57 one, then classic keywords
    if _hyprctl(["eval", LUA_RULE]) or _hyprctl(["eval", LUA_RULE_NO_GLOW]):
        return True
    ok = [_hyprctl(["keyword", "windowrulev2", f"{r},class:^({APP_CLASS})$"]) for r in CLASSIC_RULES]
    return any(ok)


# Give the panel keyboard focus (Wayland ignores Qt's own activate request) without moving the mouse
def focus_panel() -> bool:
    if not is_hyprland():
        return False
    warps = not _no_warps()
    if warps:
        _set_no_warps(True)     # focusing a window would otherwise warp the cursor to its center
    lua = f'hl.dispatch(hl.dsp.focus({{ window = "class:^({APP_CLASS})$" }}))'
    ok = _hyprctl(["eval", lua]) or _hyprctl(["dispatch", "focuswindow", f"class:^({APP_CLASS})$"])
    if warps:
        _set_no_warps(False)    # give the user's setting back
    return ok


# The user's cursor:no_warps value (True when Hyprland never moves the cursor)
def _no_warps() -> bool:
    try:
        r = subprocess.run(["hyprctl", "-j", "getoption", "cursor:no_warps"], capture_output=True, text=True, timeout=2)
        return bool(json.loads(r.stdout).get("bool", False))
    except (OSError, ValueError, AttributeError, subprocess.TimeoutExpired):
        return False


# Turn cursor warping off or on for this session (Lua config first, then classic keyword)
def _set_no_warps(on: bool) -> None:
    v = "true" if on else "false"
    if not _hyprctl(["eval", f"hl.config({{ cursor = {{ no_warps = {v} }} }})"]):
        _hyprctl(["keyword", "cursor:no_warps", v])


# Cursor position as (x, y), or None when hyprctl cannot tell
def cursor_pos() -> tuple[int, int] | None:
    try:
        r = subprocess.run(["hyprctl", "cursorpos"], capture_output=True, text=True, timeout=2)
        x, y = r.stdout.strip().split(",")
        return int(x), int(y)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
