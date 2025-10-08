"""Fan platform for SmartThings Community Edition."""

from __future__ import annotations

import logging
from typing import Any, Optional
import math

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import DOMAIN, ATTRIBUTION, DEVICE_VERSION, get_device_capabilities
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

# SmartThings fan speed values (ordered from low to high)
SMARTTHINGS_FAN_SPEEDS = ["low", "medium", "high"]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SmartThings fan platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []
    for device_id, device in coordinator.devices.items():
        capability_ids = get_device_capabilities(device)

        # Check for fan capabilities
        if "fanSpeed" in capability_ids:
            _LOGGER.info(
                "Creating fan speed control for device %s",
                device.get("label", device_id),
            )
            entities.append(SmartThingsFanSpeedControl(coordinator, api, device_id))
        elif "switch" in capability_ids:
            # Check if this is actually a fan device by checking device type
            device_type = device.get("deviceTypeName", "").lower()
            if any(
                fan_type in device_type for fan_type in ["fan", "ventilator", "exhaust"]
            ):
                _LOGGER.info(
                    "Creating simple fan switch for device %s",
                    device.get("label", device_id),
                )
                entities.append(SmartThingsFanSwitch(coordinator, api, device_id))

    async_add_entities(entities)


class SmartThingsFanSpeedControl(CoordinatorEntity, FanEntity):
    """Representation of a SmartThings fan with speed control."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_speed_count = len(SMARTTHINGS_FAN_SPEEDS)

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the fan."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_fan_speed"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Fan"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the fan."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("label", device.get("name", "Fan"))

    @property
    def supported_features(self) -> FanEntityFeature:
        """Flag supported features."""
        return FanEntityFeature.SET_SPEED

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if the fan is on."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        # Check fanSpeed capability first
        for component_id, component_status in status.items():
            if "fanSpeed" in component_status:
                fan_speed = (
                    component_status["fanSpeed"].get("fanSpeed", {}).get("value")
                )
                return fan_speed is not None and fan_speed != "off" and fan_speed != 0

        # Fall back to switch capability if present
        for component_id, component_status in status.items():
            if "switch" in component_status:
                switch_state = component_status["switch"].get("switch", {}).get("value")
                return switch_state == "on"

        return False

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "fanSpeed" in component_status:
                fan_speed = (
                    component_status["fanSpeed"].get("fanSpeed", {}).get("value")
                )

                if fan_speed is None or fan_speed == "off":
                    return 0

                # Handle numeric values (0-100 or 0-5 range)
                if isinstance(fan_speed, (int, float)):
                    # If it's in 0-5 range, convert to percentage
                    if fan_speed <= 5:
                        return int(fan_speed * 20) if fan_speed > 0 else 0
                    # If it's already in 0-100 range
                    elif fan_speed <= 100:
                        return int(fan_speed)
                    else:
                        return 100

                # Handle string values
                if isinstance(fan_speed, str):
                    try:
                        # Try to convert string to int first
                        numeric_speed = int(fan_speed)
                        if numeric_speed <= 5:
                            return int(numeric_speed * 20) if numeric_speed > 0 else 0
                        elif numeric_speed <= 100:
                            return int(numeric_speed)
                        else:
                            return 100
                    except ValueError:
                        # Handle named speeds (low, medium, high)
                        if fan_speed.lower() in SMARTTHINGS_FAN_SPEEDS:
                            return ordered_list_item_to_percentage(
                                SMARTTHINGS_FAN_SPEEDS, fan_speed.lower()
                            )

        return 0

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_turn_on(
        self,
        percentage: Optional[int] = None,
        preset_mode: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        try:
            if percentage is not None:
                await self.async_set_percentage(percentage)
            else:
                # Turn on at medium speed if no percentage specified
                await self._api.send_device_command(
                    self._device_id,
                    "fanSpeed",
                    "setFanSpeed",
                    [2],  # Medium speed (assuming 0-4 scale)
                )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on fan %s: %s", self._device_id, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "fanSpeed",
                "setFanSpeed",
                [0],  # Off
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off fan %s: %s", self._device_id, err)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage."""
        try:
            if percentage == 0:
                fan_speed = 0
            else:
                # Convert percentage to 1-4 scale (0 is off)
                fan_speed = math.ceil(percentage / 25)
                fan_speed = max(1, min(4, fan_speed))

            await self._api.send_device_command(
                self._device_id,
                "fanSpeed",
                "setFanSpeed",
                [fan_speed],
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set fan speed %s: %s", self._device_id, err)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:fan"


class SmartThingsFanSwitch(CoordinatorEntity, FanEntity):
    """Representation of a simple SmartThings fan with only on/off control."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the fan."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_fan_switch"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Fan"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the fan."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("label", device.get("name", "Fan"))

    @property
    def supported_features(self) -> FanEntityFeature:
        """Flag supported features."""
        return FanEntityFeature(0)  # Only on/off, no speed control

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if the fan is on."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {}).get("main", {}).get("switch", {})
        switch_state = status.get("switch", {}).get("value")
        return switch_state == "on"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_turn_on(
        self,
        percentage: Optional[int] = None,
        preset_mode: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "switch",
                "on",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on fan %s: %s", self._device_id, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "switch",
                "off",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off fan %s: %s", self._device_id, err)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:fan"
