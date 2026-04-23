# Standard Library
from pathlib import Path

# Plugins devices IOT for HHC_N818OP Client
from daemon_hhc_n818op.plugins.meross.meross_client_cloud_mqtt import PluginMeross as Plugin  # pylint: disable=no-name-in-module

__all__ = ["Plugin"]

MEROSS_FOLDER = Path(__file__).parent
