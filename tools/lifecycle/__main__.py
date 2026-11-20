import sys
from pathlib import Path

# Run as `python tools/lifecycle`, so the package's parent goes on the path first.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lifecycle.cli import main

sys.exit(main())
