"""Cover platform for SmartThings Community Edition."""

from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntity,
    CoverEntityFeature,
    CoverDeviceClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, ATTRIBUTION, DEVICE_VERSION, get_device_capabilities
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SmartThings cover platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []
    for device_id, device in coordinator.devices.items():
        capability_ids = get_device_capabilities(device)

        # Check for cover capabilities
        if "windowShade" in capability_ids:
            _LOGGER.info(
                "Creating window shade cover for device %s",
                device.get("label", device_id),
            )
            entities.append(SmartThingsWindowShadeCover(coordinator, api, device_id))
        elif "doorControl" in capability_ids:
            _LOGGER.info(
                "Creating door control cover for device %s",
                device.get("label", device_id),
            )
            entities.append(SmartThingsDoorControlCover(coordinator, api, device_id))
        elif "garageDoorControl" in capability_ids:
            _LOGGER.info(
                "Creating garage door cover for device %s",
                device.get("label", device_id),
            )
            entities.append(SmartThingsGarageDoorCover(coordinator, api, device_id))

    async_add_entities(entities)


class SmartThingsWindowShadeCover(CoordinatorEntity, CoverEntity):
    """Representation of a SmartThings window shade."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = CoverDeviceClass.SHADE

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the cover."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_window_shade"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Window Shade"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the cover."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("label", device.get("name", "Window Shade"))

    @property
    def supported_features(self) -> CoverEntityFeature:
        """Flag supported features."""
        device = self.coordinator.devices.get(self._device_id, {})
        capability_ids = get_device_capabilities(device)

        features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

        if "windowShadeLevel" in capability_ids:
            features |= CoverEntityFeature.SET_POSITION

        # Check if device supports stop
        status = device.get("status", {})
        for component_id, component_status in status.items():
            if "windowShade" in component_status:
                # If we have pause capability or stop is mentioned
                features |= CoverEntityFeature.STOP
                break

        return features

    @property
    def current_cover_position(self) -> Optional[int]:
        """Return current position of cover."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        # Check for windowShadeLevel first (more precise)
        for component_id, component_status in status.items():
            if "windowShadeLevel" in component_status:
                level = (
                    component_status["windowShadeLevel"]
                    .get("shadeLevel", {})
                    .get("value")
                )
                if level is not None:
                    return int(level)

        # Fall back to windowShade state
        for component_id, component_status in status.items():
            if "windowShade" in component_status:
                window_shade = (
                    component_status["windowShade"].get("windowShade", {}).get("value")
                )
                if window_shade == "open":
                    return 100
                elif window_shade == "closed":
                    return 0
                elif window_shade == "partially open":
                    return 50

        return None

    @property
    def is_closed(self) -> Optional[bool]:
        """Return if the cover is closed."""
        position = self.current_cover_position
        if position is not None:
            return position == 0

        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "windowShade" in component_status:
                window_shade = (
                    component_status["windowShade"].get("windowShade", {}).get("value")
                )
                return window_shade == "closed"

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "windowShade",
                "open",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to open cover %s: %s", self._device_id, err)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "windowShade",
                "close",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to close cover %s: %s", self._device_id, err)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "windowShade",
                "pause",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to stop cover %s: %s", self._device_id, err)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        position = kwargs.get(ATTR_POSITION)
        if position is None:
            return

        try:
            await self._api.send_device_command(
                self._device_id,
                "windowShadeLevel",
                "setShadeLevel",
                [position],
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set cover position %s: %s", self._device_id, err)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:window-shutter"


class SmartThingsDoorControlCover(CoordinatorEntity, CoverEntity):
    """Representation of a SmartThings door control."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = CoverDeviceClass.DOOR

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the cover."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_door_control"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Door Control"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the cover."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("label", device.get("name", "Door Control"))

    @property
    def supported_features(self) -> CoverEntityFeature:
        """Flag supported features."""
        return CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

    @property
    def is_closed(self) -> Optional[bool]:
        """Return if the cover is closed."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "doorControl" in component_status:
                door = component_status["doorControl"].get("door", {}).get("value")
                return door == "closed"

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "doorControl",
                "open",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to open door %s: %s", self._device_id, err)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "doorControl",
                "close",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to close door %s: %s", self._device_id, err)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:door"


class SmartThingsGarageDoorCover(CoordinatorEntity, CoverEntity):
    """Representation of a SmartThings garage door."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = CoverDeviceClass.GARAGE

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the cover."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_garage_door"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Garage Door"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the cover."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("label", device.get("name", "Garage Door"))

    @property
    def supported_features(self) -> CoverEntityFeature:
        """Flag supported features."""
        return CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

    @property
    def is_closed(self) -> Optional[bool]:
        """Return if the cover is closed."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "garageDoorControl" in component_status:
                door = (
                    component_status["garageDoorControl"].get("door", {}).get("value")
                )
                return door == "closed"

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "garageDoorControl",
                "open",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to open garage door %s: %s", self._device_id, err)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "garageDoorControl",
                "close",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to close garage door %s: %s", self._device_id, err)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:garage"
