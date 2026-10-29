"""Allow ``python -m qtax``."""

import sys

from .cli import main

sys.exit(main())
