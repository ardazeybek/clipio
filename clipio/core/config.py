"""Reads user settings (config.toml), merges them with defaults and updates single values."""
import sys

from . import paths

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

DEFAULT_HOTKEY = {"darwin": "cmd+shift+v", "win32": "ctrl+shift+v"}.get(sys.platform, "super+v")

DEFAULTS = {
    "retention_days": 14,        # unpinned items are deleted after this many days
    "max_items": 500,            # most items to keep
    "max_text_kb": 1024,         # larger texts are not saved
    "max_image_mb": 25,          # larger images are not saved
    "max_images_total_mb": 1024, # total size limit for all images
    "persist": True,             # restore the clipboard when the source app empties it
    "hotkey": DEFAULT_HOTKEY,    # global shortcut that opens the panel
    "ignore_apps": [],           # apps whose copies are never saved
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
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        pass
    return cfg


# Update one integer setting in the file (append it if missing), keeping comments
def set_int(key: str, value: int) -> None:
    write_default_if_missing()
    f = paths.config_file()
    lines = f.read_text(encoding="utf-8").splitlines()
    new = f"{key} = {int(value)}"
    for i, line in enumerate(lines):
        if line.split("=")[0].strip() == key:
            comment = line[line.index("#"):] if "#" in line else ""
            lines[i] = (new.ljust(29) + comment).rstrip()
            break
    else:
        lines.append(new)
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
