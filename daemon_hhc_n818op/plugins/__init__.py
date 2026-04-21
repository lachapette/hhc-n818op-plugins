# Expose hhc_n818op submodule from the installed hhc-n818op-standalone package
# Standard Library
import sys
from pathlib import Path

# Add the site-packages directory to sys.path to ensure we can import from the installed package
site_packages = Path(__file__).parent.parent.parent
if site_packages not in sys.path:
    sys.path.insert(0, site_packages.as_posix())

# Import the hhc_n818op submodule from the installed package
try:
    # Plugins devices IOT for HHC_N818OP Client
    import daemon_hhc_n818op.hhc_n818op as _hhc_n818op_module

    hhc_n818op_standalone = _hhc_n818op_module
except (ImportError, AttributeError):
    # If still not found, the submodule will be None
    hhc_n818op_standalone = None
