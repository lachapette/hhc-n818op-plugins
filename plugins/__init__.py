# Plugins devices IOT for HHC-N818OP
# Standard Library
import sys
from pathlib import Path

PLUGINS_ROOT_DIR: Path = Path(__file__).parent
if PLUGINS_ROOT_DIR not in sys.path:
    sys.path.insert(0, PLUGINS_ROOT_DIR.parent.as_posix())
