# Standard Library
import json
import logging
from pathlib import Path
from typing import Dict, Optional

# Third Party Libraries
from hhc_n818op.relay_client import PluginMQTT
from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager
from meross_iot.model.credentials import MerossCloudCreds

# Plugins devices IOT for HHC_N818OP Client
from daemon_hhc_n818op.plugins.meross import MEROSS_FOLDER

MFA_CODE = "meross_mfa_code"
PASSWORD = "meross_password"
LOGIN = "meross_login"
URL_REGION = "meross_url_region"
MQTT_DOMAIN = "mqtt_domain"
DOMAIN = "domain"
ISSUED_ON = "issued_on"
USER_EMAIL = "user_email"
USER_ID = "user_id"
KEY = "key"
TOKEN = "token"
MEROSS_PROFILE = "meross_profile.json"
MEROSS_REGISTRY_DUMP = "meross_registry.json"
MEROSS_CLOUD_CREDS = "meross_cloud_credentials.json"
UTF8 = "utf-8" ""


class PluginMeross(PluginMQTT):
    """
    A plugin for managing Meross devices via MQTT.

    This class provides methods to interact with Meross devices, including
    checking device status, switching devices on/off, and managing device connections.
    """

    def __init__(self):
        """
        Initializes the PluginMeross instance.
        """
        super().__init__()
        # Parent class PluginMQTT is initialized implicitly

    @staticmethod
    def _device_is_on(meross_device) -> bool:
        """
        Checks if a Meross device is on.

        Args:
            meross_device: The Meross device to check.

        Returns:
            bool: True if the device is on, False otherwise.
        """
        if hasattr(meross_device, "is_on"):
            try:
                status = meross_device.is_on(channel=0)
            except TypeError:
                status = meross_device.is_on()
            if status is not None:
                return bool(status)
        return False

    async def get_manager_mqtt(self) -> MerossManager:
        """
        Gets the Meross manager for MQTT communication.

        Returns:
            MerossManager: The Meross manager instance.
        """
        manager: MerossManager

        if Path(MEROSS_FOLDER, MEROSS_REGISTRY_DUMP).exists() and Path(MEROSS_FOLDER, MEROSS_CLOUD_CREDS).exists():
            creds = json.load(open(Path(MEROSS_FOLDER, MEROSS_CLOUD_CREDS), "r"))
            meross_cloud_creds = MerossCloudCreds(creds[TOKEN], creds[KEY], creds[USER_ID], creds[USER_EMAIL], creds[ISSUED_ON], creds[DOMAIN], creds[MQTT_DOMAIN])
            http_api_client = MerossHttpClient(meross_cloud_creds)
            # Setup and start the device manager
            manager = MerossManager(http_client=http_api_client)
            await manager.async_init()
            manager.load_devices_from_dump(Path(MEROSS_FOLDER, MEROSS_REGISTRY_DUMP))
            logging.info("Meross registry dump loaded.")
        else:
            profile_creds = json.load(open(Path(MEROSS_FOLDER, MEROSS_PROFILE), "r"))
            # Setup the HTTP client API from user-password
            http_api_client = await MerossHttpClient.async_from_user_password(profile_creds[URL_REGION], profile_creds[LOGIN], profile_creds[PASSWORD], mfa_code=profile_creds[MFA_CODE])

            # Setup and start the device manager
            manager = MerossManager(http_client=http_api_client)
            await manager.async_init()

            # Discover devices.
            await manager.async_device_discovery()
            # Dump the registry information into a test.dump file
            manager.dump_device_registry(Path(MEROSS_FOLDER, MEROSS_REGISTRY_DUMP))
            creds = open(MEROSS_CLOUD_CREDS, "w+")
            creds.write(Path(MEROSS_FOLDER, str(http_api_client.cloud_credentials)).as_posix())

        return manager

    async def disconnect(self):
        """
        Disconnects the Meross manager.
        """
        await self.manager.close()

    async def status(self, device_name: Optional[str] = None) -> bool:
        """
        Gets the status of a Meross device.

        Args:
            device_name (str, optional): The name of the device to check. Defaults to None.

        Returns:
            bool: True if the device is on, False otherwise.
        """
        is_switched_on = False
        devices = self.manager.find_devices(device_name=device_name)
        for meross_device in devices:
            await meross_device.async_update()
            is_switched_on = self._device_is_on(meross_device)
        return is_switched_on

    async def status_all(self) -> Dict[str, bool]:
        """
        Gets the status of all Meross devices.

        Returns:
            Dict[str, bool]: A dictionary mapping device names to their status.
        """
        devices_status: Dict[str, bool] = {}
        all_devices = self.manager.find_devices()
        for meross_device in all_devices:
            await meross_device.async_update()
            devices_status.update({meross_device.name: self._device_is_on(meross_device)})
        return devices_status

    @staticmethod
    async def list_devices(manager: MerossManager):
        """
        Lists all Meross devices managed by the manager.

        Args:
            manager (MerossManager): The Meross manager instance.
        """
        meross_devices = manager.find_devices()
        logging.info("I've found the following devices:")

        for meross_device in meross_devices:
            logging.info(f"- {meross_device.name} ({meross_device.type}): {meross_device.online_status}")

    async def switch_on(self, device_name: str):
        """
        Switches a Meross device on.

        Args:
            device_name (str): The name of the device to switch on.
        """
        devices = self.manager.find_devices(device_name=device_name)
        for meross_device in devices:
            logging.info(f"- {meross_device.name} ({meross_device.type}): {meross_device.online_status}")
            # The first time we play with a device, we must update its status
            await meross_device.async_update()
            logging.info(f"Turning on {meross_device.name}...")
            await meross_device.async_turn_on(channel=0)
            logging.info(f"{meross_device.name} is turned on.")

    async def switch_off(self, device_name: str):
        """
        Switches a Meross device off.

        Args:
            device_name (str): The name of the device to switch off.
        """
        devices = self.manager.find_devices(device_name=device_name)
        for meross_device in devices:
            logging.info(f"- {meross_device.name} ({meross_device.type}): {meross_device.online_status}")
            # The first time we play with a device, we must update its status
            await meross_device.async_update()
            # We can now start playing with that
            logging.info(f"Turning off {meross_device.name}...")
            await meross_device.async_turn_off(channel=0)
            logging.info(f"{meross_device.name} is turned off.")

    async def toggle_on_off(self, device_name: str, on_off_forced: bool) -> bool:
        """
        Toggles a Meross device on or off.

        Args:
            device_name (str): The name of the device to toggle.
            on_off_forced (bool): If True, forces the device on. If False, forces the device off.

        Returns:
            bool: True if the device is on, False otherwise.
        """
        is_switched_on = False
        devices = self.manager.find_devices(device_name=device_name)
        for meross_device in devices:
            await meross_device.async_update()

            if on_off_forced:
                await meross_device.async_turn_on(channel=0)
                is_switched_on = True
                logging.info(f"{meross_device.name} is switched on.")
                continue

            if not on_off_forced:
                await meross_device.async_turn_off(channel=0)
                is_switched_on = False
                logging.info(f"{meross_device.name} is switched off.")
                continue

            if self._device_is_on(meross_device):
                await meross_device.async_turn_off(channel=0)
                is_switched_on = False
                logging.info(f"{meross_device.name} is turned off.")
            else:
                await meross_device.async_turn_on(channel=0)
                is_switched_on = True
                logging.info(f"{meross_device.name} is turned on.")
        return is_switched_on
