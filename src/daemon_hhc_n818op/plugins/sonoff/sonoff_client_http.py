# Standard Library
import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

# Third Party Libraries
import requests
from requests.auth import HTTPBasicAuth

try:
    # Third Party Libraries
    from daemon_hhc_n818op.relay_plugins import PluginHTTP
except ImportError:
    # Third Party Libraries
    from daemon_hhc_n818op.hhc_n818op.relay_plugins import PluginHTTP

SONOFF_FOLDER = Path(__file__).parent
SONOFF_CONFIG_FOLDER = Path(SONOFF_FOLDER, "config")


class PluginSonoff(PluginHTTP):
    """
    A plugin for managing Sonoff 4CHPRO devices with Tasmota firmware via HTTP.

    This class provides methods to interact with Sonoff 4CHPRO devices,
    including checking device status and switching channels on/off.
    Supports up to 4 channels (1-4).
    """

    HTTP = "http://"
    HOST = "sonoff_host"
    PORT = "sonoff_port"
    USERNAME = "sonoff_username"
    PASSWORD = "sonoff_password"
    DEVICE_TOPIC = "sonoff_device_topic"

    POWER_ON = "ON"
    POWER_OFF = "OFF"
    POWER_TOGGLE = "Toggle"
    CHANNEL = "channel"

    # Tasmota HTTP API endpoints
    CMD_POWER = "Power"

    def __init__(self):
        """
        Initializes the PluginSonoff instance.
        """
        super().__init__()
        sonoff_user_config_file = Path(SONOFF_CONFIG_FOLDER, "sonoff_profile.json")
        profile_creds = json.load(open(sonoff_user_config_file, "r"))
        self.host = profile_creds[PluginSonoff.HOST]
        self.port = profile_creds[PluginSonoff.PORT]
        self.username = profile_creds.get(PluginSonoff.USERNAME, "")
        self.password = profile_creds.get(PluginSonoff.PASSWORD, "")
        self.device_topic = profile_creds.get(PluginSonoff.DEVICE_TOPIC, "")
        self.base_url = f"{PluginSonoff.HTTP}{self.host}:{self.port}"
        self.enabled = True

    def _get_auth(self) -> Dict[str, Any]:
        """
        Gets the authentication headers if username/password are configured.

        Returns:
            Dict[str, Any]: Authentication headers or empty dict.
        """
        if self.username and self.password:
            return {"Authorization": HTTPBasicAuth(self.username, self.password)}
        return {}

    def _build_url(self, command: str, channel: Optional[int] = None) -> str:
        """
        Builds the Tasmota HTTP URL for a command.

        Args:
            command (str): The Tasmota command.
            channel (int, optional): The channel number (1-4). Defaults to None (all channels).

        Returns:
            str: The full URL.
        """
        if channel is not None:
            # Channel is 1-based in Tasmota
            cmd = f"{command}{channel}"
        else:
            cmd = command
        return f"{self.base_url}/cm?cmnd={cmd}"

    def _execute_command(self, command: str, channel: Optional[int] = None, param: Optional[str] = None) -> requests.Response:
        """
        Executes a Tasmota HTTP command.

        Args:
            command (str): The Tasmota command.
            channel (int, optional): The channel number (1-4). Defaults to None.
            param (str, optional): Additional parameter for the command.

        Returns:
            requests.Response: The response from the device.
        """
        url = self._build_url(command, channel)
        if param:
            url = f"{url}%20{param}"

        headers: Mapping = self._get_auth()
        return requests.get(url, headers=headers, timeout=5)

    @staticmethod
    def _get_channel_status_from_dict(result: Dict[str, Any], channel: Optional[int]) -> Optional[bool]:
        """
        Extracts channel status from a dictionary result.

        Args:
            result (Dict[str, Any]): The dictionary to search in.
            channel (int, optional): The channel number to check.

        Returns:
            Optional[bool]: True if ON, False if OFF, None if not found.
        """
        if channel is not None:
            key = f"{PluginSonoff.CMD_POWER}{channel}"
            value = result.get(key, PluginSonoff.POWER_OFF)
            if value is not None:
                return value.upper() == PluginSonoff.POWER_ON
            return None

        # If no specific channel, check all channels 1-4
        for i in range(1, 5):
            key = f"{PluginSonoff.CMD_POWER}{i}"
            if key in result:
                return result[key].upper() == PluginSonoff.POWER_ON

        # Check POWER key
        power_value = result.get(PluginSonoff.CMD_POWER, PluginSonoff.POWER_OFF)
        if power_value is not None:
            return power_value.upper() == PluginSonoff.POWER_ON

        return None

    @staticmethod
    def _decode_power_response(response: requests.Response, channel: Optional[int] = None) -> bool:
        """
        Decodes the power status response from Tasmota.

        Args:
            response (requests.Response): The response from the device.
            channel (int, optional): The channel number to check. Defaults to None (first channel).

        Returns:
            bool: True if the channel is ON, False otherwise.
        """
        response.raise_for_status()
        try:
            result = response.json()
            if isinstance(result, dict):
                status = PluginSonoff._get_channel_status_from_dict(result, channel)
                if status is not None:
                    return status
                return False

            if isinstance(result, list) and len(result) > 0:
                first = result[0]
                if isinstance(first, dict):
                    status = PluginSonoff._get_channel_status_from_dict(first, channel)
                    if status is not None:
                        return status
                    return False

            return False
        except (ValueError, KeyError):
            # Try plain text response
            text = response.text.strip()
            return text.upper() == PluginSonoff.POWER_ON

    def _disable_plugin(self, reason: str) -> bool:
        """
        Disables the plugin due to an error.

        Args:
            reason (str): The reason for disabling the plugin.

        Returns:
            bool: False, indicating the plugin is disabled.
        """
        self.enabled = False
        logging.warning(f"Sonoff HTTP plugin disabled for host {self.host}: {reason}")
        return False

    def _request_status(self, channel: Optional[int] = None) -> bool:
        """
        Requests the status of a Sonoff channel.

        Args:
            channel (int, optional): The channel number (1-4). Defaults to None (first channel).

        Returns:
            bool: The status of the channel.
        """
        if not self.enabled:
            return False
        try:
            # First try to get the full state
            response = self._execute_command("", param="State")
            if response.status_code == 401:
                # Authentication failed, try without auth
                self.username = ""
                self.password = ""
                response = self._execute_command("", param="State")
            return self._decode_power_response(response, channel)
        except (requests.RequestException, ValueError, KeyError) as exc:
            return self._disable_plugin(str(exc))

    def _request_power(self, state: str, channel: Optional[int] = None) -> bool:
        """
        Requests to set the power state of a Sonoff channel.

        Args:
            state (str): The power state (ON, OFF, Toggle).
            channel (int, optional): The channel number (1-4). Defaults to None (all channels).

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.enabled:
            return False
        try:
            response = self._execute_command(PluginSonoff.CMD_POWER, channel, state)
            if response.status_code == 401:
                # Authentication failed, try without auth
                self.username = ""
                self.password = ""
                response = self._execute_command(PluginSonoff.CMD_POWER, channel, state)
            response.raise_for_status()
            # Verify the state was set correctly
            return self._decode_power_response(response, channel)
        except (requests.RequestException, ValueError, KeyError) as exc:
            return self._disable_plugin(str(exc))

    async def get_manager_http(self) -> str | None:
        """
        Gets the URL for the Sonoff device.

        Returns:
            str | None: The base URL of the Sonoff device, or None if the device is unavailable.
        """
        ping_result = subprocess.run(
            [shutil.which("ping") or "ping", "-c", "1", "-W", "1", self.host],  # nosec B603
            shell=False,
            capture_output=True,
            text=True,
            check=False,
        )
        if ping_result.returncode != 0:
            self.enabled = False
            logging.warning(f"SonOff host {self.host} is unavailable over ICMP, HTTP plugin disabled")
            return None
        return self.base_url

    async def disconnect(self, **kwargs) -> None:
        """
        Disconnects the Sonoff device.
        """

    async def status(self, **kwargs) -> bool:
        """
        Gets the status of the Sonoff device.
        If channel is specified in kwargs, checks that specific channel.
        Otherwise checks the first channel.

        Args:
            **kwargs: channel (int): The channel number (1-4).

        Returns:
            bool: The status of the specified channel or first channel.
        """
        channel = kwargs.get(PluginSonoff.CHANNEL, 1)
        return self._request_status(channel)

    async def status_all(self) -> Dict[str, bool]:
        """
        Gets the status of all channels on the Sonoff 4CHPRO device.

        Returns:
            Dict[str, bool]: A dictionary mapping channel names to their status.
        """
        devices_status: Dict[str, bool] = {}
        for channel_id in range(1, 5):
            devices_status[f"{PluginSonoff.CHANNEL}_{channel_id}"] = self._request_status(channel_id)
        return devices_status

    async def switch_on(self, **kwargs) -> bool:
        """
        Switches a Sonoff channel on.

        Args:
            **kwargs: channel (int): The channel number (1-4). Defaults to 1.

        Returns:
            bool: True if successful, False otherwise.
        """
        channel = kwargs.get(PluginSonoff.CHANNEL, 1)
        return self._request_power(PluginSonoff.POWER_ON, channel)

    async def switch_off(self, **kwargs) -> bool:
        """
        Switches a Sonoff channel off.

        Args:
            **kwargs: channel (int): The channel number (1-4). Defaults to 1.

        Returns:
            bool: True if successful, False otherwise.
        """
        channel = kwargs.get(PluginSonoff.CHANNEL, 1)
        return self._request_power(PluginSonoff.POWER_OFF, channel)

    async def toggle_on_off(self, **kwargs) -> bool:
        """
        Toggles the status of a Sonoff channel.

        Args:
            **kwargs: channel (int): The channel number (1-4). Defaults to 1.

        Returns:
            bool: The new status of the channel.
        """
        channel = kwargs.get(PluginSonoff.CHANNEL, 1)
        return self._request_power(PluginSonoff.POWER_TOGGLE, channel)
