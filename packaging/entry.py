"""Entry point of the packaged app: the same `clipio` command, plus setup when double-clicked."""
import sys

from clipio.cli import main

if __name__ == "__main__":
    sys.exit(main())
