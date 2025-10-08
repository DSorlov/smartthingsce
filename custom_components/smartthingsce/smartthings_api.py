"""SmartThings API client."""

import logging
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientSession

from .const import (
    API_BASE_URL,
    API_DEVICES,
    API_LOCATIONS,
    API_ROOMS,
    API_SCENES,
)

_LOGGER = logging.getLogger(__name__)


class SmartThingsAPIError(Exception):
    """Exception raised for SmartThings API errors."""


class SmartThingsAPI:
    """SmartThings API client."""

    def __init__(self, access_token: str, session: ClientSession) -> None:
        """Initialize the API client."""
        self._access_token = access_token
        self._session = session
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make an API request."""
        try:
            _LOGGER.debug("Making %s request to %s", method, url)
            async with self._session.request(
                method,
                url,
                headers=self._headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 401:
                    _LOGGER.error("Authentication failed. Please check your token.")
                    raise SmartThingsAPIError("Invalid or expired access token (401)")

                response.raise_for_status()

                if response.status == 204:
                    return None

                result = await response.json()
                _LOGGER.debug("Request successful, status: %s", response.status)
                return result

        except aiohttp.ClientResponseError as err:
            if err.status == 401:
                _LOGGER.error("Authentication failed: Invalid token")
                raise SmartThingsAPIError("Invalid or expired access token")
            elif err.status == 403:
                _LOGGER.error("Access forbidden: Check token permissions")
                raise SmartThingsAPIError("Token does not have required permissions")
            else:
                _LOGGER.error("API request failed: %s - %s", err.status, err.message)
                raise SmartThingsAPIError(
                    f"API request failed: {err.status} - {err.message}"
                )
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error during API request: %s", err)
            raise SmartThingsAPIError(f"Network error: {err}")
        except Exception as err:
            _LOGGER.error("Unexpected error during API request: %s", err)
            raise SmartThingsAPIError(f"Unexpected error: {err}")

    async def get_locations(self) -> List[Dict[str, Any]]:
        """Get all locations."""
        response = await self._request("GET", API_LOCATIONS)
        return response.get("items", [])

    async def get_location(self, location_id: str) -> Dict[str, Any]:
        """Get a specific location."""
        url = f"{API_LOCATIONS}/{location_id}"
        return await self._request("GET", url)

    async def get_rooms(self, location_id: str) -> List[Dict[str, Any]]:
        """Get rooms for a location."""
        url = API_ROOMS.format(location_id=location_id)
        response = await self._request("GET", url)
        return response.get("items", [])

    async def get_devices(
        self, location_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all devices, optionally filtered by location."""
        params = f"?locationId={location_id}" if location_id else ""
        url = f"{API_DEVICES}{params}"
        response = await self._request("GET", url)
        return response.get("items", [])

    async def get_device(self, device_id: str) -> Dict[str, Any]:
        """Get a specific device."""
        url = f"{API_DEVICES}/{device_id}"
        return await self._request("GET", url)

    async def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """Get device status."""
        url = f"{API_DEVICES}/{device_id}/status"
        response = await self._request("GET", url)
        return response.get("components", {})

    async def get_device_health(self, device_id: str) -> Dict[str, Any]:
        """Get device health."""
        url = f"{API_DEVICES}/{device_id}/health"
        return await self._request("GET", url)

    async def send_device_command(
        self,
        device_id: str,
        capability: str,
        command: str,
        arguments: Optional[List[Any]] = None,
        component: str = "main",
    ) -> Dict[str, Any]:
        """Send a command to a device."""
        url = f"{API_DEVICES}/{device_id}/commands"

        data = {
            "commands": [
                {
                    "component": component,
                    "capability": capability,
                    "command": command,
                    "arguments": arguments or [],
                }
            ]
        }

        _LOGGER.debug(
            "Sending command to device %s: capability=%s, command=%s, args=%s",
            device_id,
            capability,
            command,
            arguments,
        )
        return await self._request("POST", url, data)

    async def get_scenes(
        self, location_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get scenes, optionally filtered by location."""
        params = f"?locationId={location_id}" if location_id else ""
        url = f"{API_SCENES}{params}"
        response = await self._request("GET", url)
        return response.get("items", [])

    async def execute_scene(self, scene_id: str) -> None:
        """Execute a scene."""
        url = f"{API_SCENES}/{scene_id}/execute"
        await self._request("POST", url)

    async def create_subscription(
        self,
        installed_app_id: str,
        source_type: str,
        capability: str,
        attribute: str,
        value: Optional[str] = None,
        location_id: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a subscription."""
        url = f"{API_BASE_URL}/installedapps/{installed_app_id}/subscriptions"

        data = {
            "sourceType": source_type,
            "device": {},
        }

        if device_id:
            data["device"]["deviceId"] = device_id
            data["device"]["componentId"] = "main"
            data["device"]["capability"] = capability
            data["device"]["attribute"] = attribute
            if value:
                data["device"]["value"] = value

        if location_id:
            data["device"]["locationId"] = location_id

        return await self._request("POST", url, data)

    async def delete_subscription(
        self,
        installed_app_id: str,
        subscription_id: str,
    ) -> None:
        """Delete a subscription."""
        url = f"{API_BASE_URL}/installedapps/{installed_app_id}/subscriptions/{subscription_id}"
        await self._request("DELETE", url)

    async def get_subscriptions(self, installed_app_id: str) -> List[Dict[str, Any]]:
        """Get all subscriptions."""
        url = f"{API_BASE_URL}/installedapps/{installed_app_id}/subscriptions"
        response = await self._request("GET", url)
        return response.get("items", [])
