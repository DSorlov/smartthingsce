"""SmartThings Community Edition Integration."""

import asyncio
import logging
import uuid
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ATTR_ARGUMENTS,
    ATTR_CAPABILITY,
    ATTR_COMMAND,
    ATTR_DEVICE_ID,
    ATTR_SCENE_ID,
    CONF_LOCATION_ID,
    CONF_WEBHOOK_ENABLED,
    DOMAIN,
    PLATFORMS,
    SERVICE_EXECUTE_SCENE,
    SERVICE_REFRESH_DEVICES,
    SERVICE_SEND_COMMAND,
    UPDATE_INTERVAL_SECONDS,
)
from .smartthings_api import SmartThingsAPI
from .webhook import WebhookManager

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


class SmartThingsCoordinator(DataUpdateCoordinator):
    """SmartThings data update coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: SmartThingsAPI,
        location_id: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        self.api = api
        self.location_id = location_id
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.rooms: Dict[str, Dict[str, Any]] = {}
        self.scenes: Dict[str, Dict[str, Any]] = {}

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from SmartThings API."""
        try:
            _LOGGER.debug("Starting data fetch from SmartThings API")

            # Fetch devices
            devices = await self.api.get_devices(self.location_id)
            _LOGGER.debug("Fetched %d devices from API", len(devices))
            self.devices = {device["deviceId"]: device for device in devices}

            # Debug: Log device information
            for device in devices:
                _LOGGER.debug("Raw device structure: %s", device)
                device_name = device.get("label", device.get("name", "Unknown"))
                device_id = device.get("deviceId", "Unknown")
                # Components is a list, find the 'main' component
                components = device.get("components", [])
                main_component = next(
                    (c for c in components if c.get("id") == "main"), None
                )
                if main_component:
                    capabilities = main_component.get("capabilities", [])
                else:
                    capabilities = []
                cap_ids = [
                    cap.get("id") if isinstance(cap, dict) else cap
                    for cap in capabilities
                ]
                _LOGGER.info(
                    "Device discovered: %s (ID: %s) with capabilities: %s",
                    device_name,
                    device_id,
                    cap_ids,
                )

            # Fetch rooms
            _LOGGER.debug("Fetching rooms")
            rooms = await self.api.get_rooms(self.location_id)
            self.rooms = {room["roomId"]: room for room in rooms}
            _LOGGER.debug("Fetched %d rooms", len(rooms))

            # Fetch scenes
            _LOGGER.debug("Fetching scenes")
            scenes = await self.api.get_scenes(self.location_id)
            self.scenes = {scene["sceneId"]: scene for scene in scenes}
            _LOGGER.debug("Fetched %d scenes", len(scenes))

            # Get device status for all devices
            _LOGGER.debug("Fetching status for %d devices", len(self.devices))
            for device_id in self.devices:
                try:
                    status = await self.api.get_device_status(device_id)
                    self.devices[device_id]["status"] = status
                    _LOGGER.debug("Device %s status: %s", device_id, status)
                except Exception as err:
                    _LOGGER.warning(
                        "Failed to get status for device %s: %s", device_id, err
                    )

            _LOGGER.debug("Data fetch completed successfully")
            return {
                "devices": self.devices,
                "rooms": self.rooms,
                "scenes": self.scenes,
            }

        except Exception as err:
            _LOGGER.error("Error in _async_update_data: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with SmartThings API: {err}")


async def async_setup(hass: HomeAssistant, config: Dict) -> bool:
    """Set up the SmartThings Community Edition component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SmartThings Community Edition from a config entry."""
    access_token = entry.data[CONF_ACCESS_TOKEN]
    location_id = entry.data[CONF_LOCATION_ID]
    webhook_enabled = entry.data.get(CONF_WEBHOOK_ENABLED, False)

    # Create API client
    session = async_get_clientsession(hass)
    api = SmartThingsAPI(access_token, session)

    # Verify API connection
    try:
        locations = await api.get_locations()
        if not any(loc["locationId"] == location_id for loc in locations):
            raise ConfigEntryNotReady("Selected location not found")
    except Exception as err:
        raise ConfigEntryNotReady(f"Failed to connect to SmartThings API: {err}")

    # Create coordinator
    coordinator = SmartThingsCoordinator(hass, api, location_id)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Ensure domain is initialized in hass.data
    hass.data.setdefault(DOMAIN, {})

    # Store coordinator and API
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
        "webhook_manager": None,
    }

    # Setup webhook if enabled
    if webhook_enabled:
        webhook_manager = WebhookManager(hass, api, coordinator, entry)
        await webhook_manager.async_setup()
        hass.data[DOMAIN][entry.entry_id]["webhook_manager"] = webhook_manager

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await async_setup_services(hass, coordinator, api)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Cleanup webhook
    webhook_manager = hass.data[DOMAIN][entry.entry_id].get("webhook_manager")
    if webhook_manager:
        await webhook_manager.async_cleanup()

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            del hass.data[DOMAIN]

    return unload_ok


async def async_setup_services(
    hass: HomeAssistant,
    coordinator: SmartThingsCoordinator,
    api: SmartThingsAPI,
) -> None:
    """Set up services for SmartThings."""

    async def send_command(call: ServiceCall) -> None:
        """Send a command to a device."""
        device_id = call.data[ATTR_DEVICE_ID]
        capability = call.data[ATTR_CAPABILITY]
        command = call.data[ATTR_COMMAND]
        arguments = call.data.get(ATTR_ARGUMENTS, [])

        try:
            await api.send_device_command(device_id, capability, command, arguments)
            await coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to send command: %s", err)

    async def execute_scene(call: ServiceCall) -> None:
        """Execute a SmartThings scene."""
        scene_id = call.data[ATTR_SCENE_ID]

        try:
            await api.execute_scene(scene_id)
        except Exception as err:
            _LOGGER.error("Failed to execute scene: %s", err)

    async def refresh_devices(call: ServiceCall) -> None:
        """Refresh device states."""
        await coordinator.async_request_refresh()

    # Register services
    hass.services.async_register(DOMAIN, SERVICE_SEND_COMMAND, send_command)
    hass.services.async_register(DOMAIN, SERVICE_EXECUTE_SCENE, execute_scene)
    hass.services.async_register(DOMAIN, SERVICE_REFRESH_DEVICES, refresh_devices)
