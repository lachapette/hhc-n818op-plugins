# Standard Library
from pathlib import Path

# Plugins devices IOT for HHC_N818OP Client
from daemon_hhc_n818op.plugins.athom.athom_smart_client_home_http import PluginAthomSmartHome as Plugin  # pylint: disable=no-name-in-module

__all__ = ["Plugin"]

ATHOM_FOLDER = Path(__file__).parent
