# Standard Library
import json
import logging
import shutil
import subprocess

# Third Party Libraries
import requests

try:
    # Third Party Libraries
    from daemon_hhc_n818op.relay_plugins import PluginHTTP
except ImportError:
    # Third Party Libraries
    from daemon_hhc_n818op.hhc_n818op.relay_plugins import PluginHTTP

PUMP_RELAY_1 = "relay_1"
PUMP_STATUS_DATA = "data"


class PluginAthomSmartHome(PluginHTTP):
    """
    A plugin for managing Athom Smart Home devices via HTTP.

    This class provides methods to interact with Athom Smart Home devices,
    including checking device status and toggling device state.
    """

    def __init__(self, host: str, port: int):
        """
        Initializes the PluginAthomSmartHome instance.

        Args:
            host (str): The hostname or IP address of the Athom device.
            port (int): The port number of the Athom device.
        """
        super().__init__()
        self.host = host
        self.port = port
        self.url = f"http://{self.host}:{self.port}/relay_do"
        self.enabled = True

    @staticmethod
    def _decode_status_response(response: requests.Response) -> bool:
        """
        Decodes the status response from the Athom device.

        Args:
            response (requests.Response): The response from the Athom device.

        Returns:
            bool: The status of the relay.

        Raises:
            ValueError: If the response payload is empty.
            KeyError: If the response does not contain the expected data.
            json.JSONDecodeError: If the response payload is not valid JSON.
        """
        response.raise_for_status()
        payload = response.content.decode().strip()
        if not payload:
            raise ValueError("empty Athom response")
        relay_status = json.loads(payload)
        return bool(relay_status[PUMP_STATUS_DATA][PUMP_RELAY_1])

    def _disable_plugin(self, reason: str) -> bool:
        """
        Disables the plugin due to an error.

        Args:
            reason (str): The reason for disabling the plugin.

        Returns:
            bool: False, indicating the plugin is disabled.
        """
        self.enabled = False
        logging.warning(f"Athom HTTP plugin disabled for host {self.host}: {reason}")
        return False

    def _request_status(self) -> bool:
        """
        Requests the status of the Athom device.

        Returns:
            bool: The status of the relay.
        """
        if not self.enabled:
            return False
        try:
            response = requests.get(self.url, params={"c": 2}, timeout=5)
            return self._decode_status_response(response)
        except (requests.RequestException, ValueError, KeyError, json.JSONDecodeError) as exc:
            return self._disable_plugin(str(exc))

    def _request_toggle(self) -> bool:
        """
        Requests to toggle the status of the Athom device.

        Returns:
            bool: The new status of the relay.
        """
        if not self.enabled:
            return False
        try:
            response = requests.get(self.url, params={"c": 1}, timeout=5)
            return self._decode_status_response(response)
        except (requests.RequestException, ValueError, KeyError, json.JSONDecodeError) as exc:
            return self._disable_plugin(str(exc))

    async def get_manager_http(self) -> str | None:
        """
        Gets the URL for the Athom device.

        Returns:
            str | None: The URL of the Athom device, or None if the device is unavailable.
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
            logging.warning(f"Athom host {self.host} is unavailable over ICMP, HTTP plugin disabled")
            return None
        return self.url

    async def disconnect(self, **kwargs) -> object:
        """
        Disconnects the Athom device.

        Returns:
            object: None, as there is no active connection to disconnect.
        """
        pass

    async def status(self, **kwargs) -> bool:
        """
        Gets the status of the Athom device.

        Returns:
            bool: The status of the relay.
        """
        return self._request_status()

    async def switch_on(self, **kwargs) -> bool:
        """
        Switches the Athom device on.

        Returns:
            bool: The new status of the relay.
        """
        if self._request_status():
            return True
        return self._request_toggle()

    async def switch_off(self, **kwargs) -> bool:
        """
        Switches the Athom device off.

        Returns:
            bool: The new status of the relay.
        """
        if not self._request_status():
            return False
        return self._request_toggle()

    async def toggle_on_off(self, **kwargs) -> bool:
        """
        Toggles the status of the Athom device.

        Returns:
            bool: The new status of the relay.
        """
        return self._request_toggle()
