# Standard Library
from pathlib import Path

# Plugins devices IOT for HHC_N818OP Client
from plugins.meross.meross_client_cloud_mqtt import PluginMeross as Plugin

__all__ = ["Plugin"]

MEROSS_FOLDER = Path(__file__).parent
