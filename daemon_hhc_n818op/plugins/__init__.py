# Expose hhc_n818op submodule from the installed hhc-n818op-standalone package
# Standard Library
import sys
from pathlib import Path

# Add the site-packages directory to sys.path to ensure we can import from the installed package
site_packages = Path(__file__).parent.parent.parent
if site_packages not in sys.path:
    sys.path.insert(0, site_packages.as_posix())
