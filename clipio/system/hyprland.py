"""Hyprland niceties: a runtime window rule so the panel floats, centered, without borders or blur."""
import subprocess

from . import is_hyprland

APP_CLASS = "clipio"

# Lua configs (Hyprland 0.54+)
LUA_RULE = ('hl.window_rule({ name = "clipio-panel", match = { class = "^clipio$" }, float = true, '
            'center = true, opacity = "1.0 override", no_blur = true, no_shadow = true, '
            'border_size = 0, rounding = 0, no_anim = true })')

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
    if _hyprctl(["eval", LUA_RULE]):
        return True
    ok = [_hyprctl(["keyword", "windowrulev2", f"{r},class:^({APP_CLASS})$"]) for r in CLASSIC_RULES]
    return any(ok)
