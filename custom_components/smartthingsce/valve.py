"""Valve platform for SmartThings Community Edition."""

from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.valve import (
    ValveEntity,
    ValveEntityFeature,
    ValveDeviceClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ATTRIBUTION, DEVICE_VERSION, get_device_capabilities

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SmartThings valve platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []
    for device_id, device in coordinator.devices.items():
        capability_ids = get_device_capabilities(device)

        # Check for valve capability
        if "valve" in capability_ids:
            # Determine valve type based on device information
            device_type = device.get("deviceTypeName", "").lower()
            device_label = device.get("label", "").lower()

            valve_class = ValveDeviceClass.WATER
            if any(
                keyword in device_type or keyword in device_label
                for keyword in ["gas", "fuel"]
            ):
                valve_class = ValveDeviceClass.GAS
            elif any(
                keyword in device_type or keyword in device_label
                for keyword in ["irrigation", "sprinkler", "garden"]
            ):
                valve_class = ValveDeviceClass.WATER

            _LOGGER.info(
                "Creating valve for device %s with class %s",
                device.get("label", device_id),
                valve_class,
            )
            entities.append(SmartThingsValve(coordinator, api, device_id, valve_class))

    async_add_entities(entities)


class SmartThingsValve(CoordinatorEntity, ValveEntity):
    """Representation of a SmartThings valve."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self, coordinator, api, device_id: str, valve_class: ValveDeviceClass
    ) -> None:
        """Initialize the valve."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_valve"
        self._attr_device_class = valve_class

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Valve"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the valve."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("label", device.get("name", "Valve"))

    @property
    def supported_features(self) -> ValveEntityFeature:
        """Flag valve features that are supported."""
        return ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE

    @property
    def is_closed(self) -> Optional[bool]:
        """Return if the valve is closed."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "valve" in component_status:
                valve_state = component_status["valve"].get("valve", {}).get("value")
                return valve_state == "closed"

        return None

    @property
    def is_closing(self) -> bool:
        """Return if the valve is closing."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "valve" in component_status:
                valve_state = component_status["valve"].get("valve", {}).get("value")
                return valve_state == "closing"

        return False

    @property
    def is_opening(self) -> bool:
        """Return if the valve is opening."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "valve" in component_status:
                valve_state = component_status["valve"].get("valve", {}).get("value")
                return valve_state == "opening"

        return False

    @property
    def current_valve_position(self) -> Optional[int]:
        """Return current position of valve (0-100)."""
        # Most SmartThings valves are binary (open/closed) but some may support positions
        if self.is_closed:
            return 0
        elif not self.is_closing and not self.is_opening:
            return 100
        else:
            return 50  # In transition

    @property
    def reports_position(self) -> bool:
        """Return if the valve reports position."""
        # Most SmartThings valves only report binary state
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})
        attributes = {}

        # Add valve-specific attributes if available
        for component_id, component_status in status.items():
            if "valve" in component_status:
                valve_data = component_status["valve"]

                # Add raw valve state
                if "valve" in valve_data:
                    attributes["valve_state"] = valve_data["valve"].get("value")

                # Add any additional valve properties
                for key, value_dict in valve_data.items():
                    if key != "valve" and isinstance(value_dict, dict):
                        if "value" in value_dict:
                            attributes[f"valve_{key}"] = value_dict["value"]

                break

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_open_valve(self, **kwargs: Any) -> None:
        """Open the valve."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "valve",
                "open",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to open valve %s: %s", self._device_id, err)

    async def async_close_valve(self, **kwargs: Any) -> None:
        """Close the valve."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "valve",
                "close",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to close valve %s: %s", self._device_id, err)

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self._attr_device_class == ValveDeviceClass.GAS:
            return "mdi:gas-cylinder"
        elif self._attr_device_class == ValveDeviceClass.WATER:
            return "mdi:water-pump"
        else:
            return "mdi:pipe-valve"
