"""Where Clipio keeps its files on each operating system (data, images, config)."""
import os
import sys
from pathlib import Path

APP = "clipio"


# Return the per-user data folder for the current operating system
def data_dir() -> Path:
    if override := os.environ.get("CLIPIO_DATA_DIR"):
        return Path(override)
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / APP
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / APP


# Return the per-user config folder for the current operating system
def config_dir() -> Path:
    if override := os.environ.get("CLIPIO_CONFIG_DIR"):
        return Path(override)
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / APP
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / APP


# Database file
def db_file() -> Path:
    return data_dir() / "clipio.db"


# Folder for copied images
def image_dir() -> Path:
    return data_dir() / "images"


# Recording is paused while this file exists
def pause_file() -> Path:
    return data_dir() / "paused"


# User settings file
def config_file() -> Path:
    return config_dir() / "config.toml"


# Create the folders Clipio writes to
def ensure_dirs() -> None:
    for d in (data_dir(), image_dir(), config_dir()):
        d.mkdir(parents=True, exist_ok=True)
