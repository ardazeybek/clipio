"""Allows running Clipio with `python -m clipio`."""
import sys

from .cli import main

sys.exit(main(sys.argv[1:]))
