"""Reads user settings (config.toml), merges them with defaults and updates single values."""
import sys

from . import paths

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

DEFAULT_HOTKEY = {"darwin": "cmd+shift+v", "win32": "ctrl+shift+v"}.get(sys.platform, "super+v")

# In-panel shortcuts: action -> key sequence (written as key_<action> in config.toml)
SHORTCUTS = {
    "paste": "Return",
    "paste_clean": "Shift+Return",
    "copy": "Ctrl+C",
    "menu": "Ctrl+M",
    "edit": "Ctrl+E",
    "mark": "Ctrl+Space",
    "pin": "Ctrl+P",
    "delete": "Delete",
    "next_tab": "Tab",
    "prev_tab": "Shift+Backtab",
    "settings": "Ctrl+,",
}

# Features the user can switch off in the settings page
FEATURES = {
    "clean_links": True,      # remove tracking parameters from copied links
    "link_titles": False,     # fetch page titles of links (sends a request to the site)
    "detect_secrets": True,   # hide and expire passwords, keys and card numbers
    "templates": True,        # fill {date}, {clipboard}… in pinned snippets
    "code_colors": True,      # color code cards
    "show_source": True,      # show the app an item came from
    "quick_numbers": True,    # Alt+1…9 pastes the first nine cards
}

DEFAULTS = {
    "retention_days": 14,        # unpinned items are deleted after this many days
    "max_items": 500,            # most items to keep
    "max_text_kb": 1024,         # larger texts are not saved
    "max_image_mb": 25,          # larger images are not saved
    "max_images_total_mb": 1024, # total size limit for all images
    "persist": True,             # restore the clipboard when the source app empties it
    "hotkey": DEFAULT_HOTKEY,    # global shortcut that opens the panel
    "ignore_apps": [],           # apps whose copies are never saved
    "secret_minutes": 5,         # copied passwords, keys and card numbers are deleted after this
    "panel_keep_minutes": 5,     # the closed panel stays loaded this long, then frees its memory
    **FEATURES,
    **{f"key_{a}": k for a, k in SHORTCUTS.items()},
}

TEMPLATE = f"""# Clipio settings
retention_days = 14          # days before unpinned items are deleted
max_items = 500              # most items to keep
max_text_kb = 1024           # larger texts are not saved
max_image_mb = 25            # larger images are not saved
max_images_total_mb = 1024   # total size limit for all images
persist = true               # restore the clipboard when the source app empties it
hotkey = "{DEFAULT_HOTKEY}"   # shortcut that opens the panel (not used on Wayland)
ignore_apps = []             # e.g. ["KeePassXC", "1Password"]
clean_links = true           # remove tracking parameters from copied links
secret_minutes = 5           # minutes before copied passwords, keys and card numbers are deleted
link_titles = false          # fetch page titles of copied links (sends a request to the site)
panel_keep_minutes = 5       # minutes the closed panel stays loaded (opens instantly), then frees its memory; 0 = free at once
# Everything else (features and in-panel shortcuts such as key_edit = "Ctrl+E")
# can be changed in the panel's settings page.
"""


# Create the settings file from the template if it does not exist
def write_default_if_missing() -> None:
    f = paths.config_file()
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(TEMPLATE, encoding="utf-8")


# Return the settings: file values on top of the defaults (a broken file falls back to defaults)
def load() -> dict:
    cfg = dict(DEFAULTS)
    try:
        with open(paths.config_file(), "rb") as f:
            cfg.update(tomllib.load(f))
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError):
        pass
    return _validated(cfg)


# Replace values of the wrong type or out of range with the defaults
def _validated(cfg: dict) -> dict:
    limits = {"retention_days": (1, 365), "max_items": (1, 100000), "max_text_kb": (1, 102400),
              "max_image_mb": (1, 1024), "max_images_total_mb": (1, 1048576),
              "secret_minutes": (1, 1440), "panel_keep_minutes": (0, 1440)}
    for key, (lo, hi) in limits.items():
        v = cfg[key]
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            cfg[key] = DEFAULTS[key]
        else:
            cfg[key] = int(max(lo, min(hi, v)))
    for key in ("persist", *FEATURES):
        if not isinstance(cfg[key], bool):
            cfg[key] = DEFAULTS[key]
    if not isinstance(cfg["hotkey"], str):
        cfg["hotkey"] = DEFAULTS["hotkey"]
    if not isinstance(cfg["ignore_apps"], list):
        cfg["ignore_apps"] = []
    cfg["ignore_apps"] = [str(a) for a in cfg["ignore_apps"]]
    for action, default in SHORTCUTS.items():
        k = f"key_{action}"
        if not isinstance(cfg[k], str) or not cfg[k].strip():
            cfg[k] = default
    return cfg


# Write a Python value in TOML syntax (int, bool, str or list of str)
def _toml(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml(str(v)) for v in value) + "]"
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


# Update one setting in the file (append it if missing), keeping comments
def set_value(key: str, value) -> None:
    write_default_if_missing()
    f = paths.config_file()
    lines = f.read_text(encoding="utf-8").splitlines()
    new = f"{key} = {_toml(value)}"
    for i, line in enumerate(lines):
        if line.split("=")[0].strip() == key:
            comment = line[line.index("#", len(line.split("#")[0])):] if "#" in line else ""
            lines[i] = (new.ljust(29) + comment).rstrip()
            break
    else:
        lines.append(new)
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")


# Update one integer setting
def set_int(key: str, value: int) -> None:
    set_value(key, int(value))
