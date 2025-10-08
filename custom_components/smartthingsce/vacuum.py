"""Vacuum platform for SmartThings Communi    for device_id, device in coordinator.devices.items():
# Get capabilities from the main component
capability_ids = get_device_capabilities(device)

# Check if this is a robot cleaner
if "robotCleanerMovement" in capability_ids:ion (Robot Cleaners)."""

import logging
from typing import Any

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DEVICE_VERSION, DOMAIN, get_device_capabilities

_LOGGER = logging.getLogger(__name__)

# SmartThings robot cleaner movement states to HA vacuum states
MOVEMENT_TO_STATE = {
    "idle": VacuumActivity.IDLE,
    "cleaning": VacuumActivity.CLEANING,
    "charging": VacuumActivity.DOCKED,
    "homing": VacuumActivity.RETURNING,
    "paused": VacuumActivity.PAUSED,
    "alarm": VacuumActivity.ERROR,
    "powerOff": VacuumActivity.IDLE,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SmartThings robot vacuum cleaners."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities = []

    for device_id, device in coordinator.devices.items():
        # Get capabilities - SmartThings API returns them as a list at device level
        capabilities = device.get("capabilities", [])
        capability_ids = [
            cap.get("id") if isinstance(cap, dict) else cap for cap in capabilities
        ]

        # Check if device is a robot cleaner
        if "robotCleanerMovement" in capability_ids:
            _LOGGER.debug(
                "Setting up robot vacuum for device %s",
                device.get("label", device_id),
            )
            entities.append(
                SmartThingsRobotVacuum(coordinator, device_id, config_entry)
            )

    if entities:
        _LOGGER.info("Adding %d robot vacuum entities", len(entities))
        async_add_entities(entities)


class SmartThingsRobotVacuum(CoordinatorEntity, StateVacuumEntity):
    """Representation of a SmartThings robot vacuum cleaner."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_supported_features = (
        VacuumEntityFeature.START
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.BATTERY
    )

    def __init__(
        self,
        coordinator,
        device_id: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the robot vacuum."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._config_entry = config_entry

        device = coordinator.data.get(device_id, {})
        self._attr_unique_id = f"{DOMAIN}_{device_id}_vacuum"
        self._attr_name = device.get("label", "Robot Vacuum")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Robot Vacuum"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def state(self) -> str | None:
        """Return the state of the vacuum cleaner."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        # Get movement state
        movement_status = status.get("robotCleanerMovement", {})
        movement = movement_status.get("robotCleanerMovement", {}).get("value")

        if movement:
            return MOVEMENT_TO_STATE.get(movement, VacuumActivity.IDLE)

        return VacuumActivity.IDLE

    @property
    def battery_level(self) -> int | None:
        """Return the battery level of the vacuum cleaner."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        battery_status = status.get("battery", {})
        battery = battery_status.get("battery", {}).get("value")

        if battery is not None:
            return int(battery)

        return None

    @property
    def fan_speed(self) -> str | None:
        """Return the fan speed of the vacuum cleaner."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        # Check for turbo mode
        turbo_status = status.get("robotCleanerTurboMode", {})
        turbo = turbo_status.get("robotCleanerTurboMode", {}).get("value")

        if turbo == "on":
            return "turbo"

        # Check for cleaning mode
        mode_status = status.get("robotCleanerCleaningMode", {})
        mode = mode_status.get("robotCleanerCleaningMode", {}).get("value")

        return mode if mode else "auto"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device specific state attributes."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        attributes = {
            "device_id": self._device_id,
        }

        # Add cleaning mode
        mode_status = status.get("robotCleanerCleaningMode", {})
        mode = mode_status.get("robotCleanerCleaningMode", {}).get("value")
        if mode:
            attributes["cleaning_mode"] = mode

        # Add turbo mode
        turbo_status = status.get("robotCleanerTurboMode", {})
        turbo = turbo_status.get("robotCleanerTurboMode", {}).get("value")
        if turbo:
            attributes["turbo_mode"] = turbo

        # Add cleaning area if available
        area_status = status.get("samsungce.robotCleanerCleaningArea", {})
        area = area_status.get("cleaningArea", {}).get("value")
        if area:
            attributes["cleaning_area"] = area

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_start(self) -> None:
        """Start or resume the cleaning task."""
        await self._send_command("robotCleanerMovement", "start")

    async def async_stop(self, **kwargs: Any) -> None:
        """Stop the cleaning task."""
        await self._send_command("robotCleanerMovement", "stop")

    async def async_pause(self) -> None:
        """Pause the cleaning task."""
        await self._send_command("robotCleanerMovement", "pause")

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Set the vacuum cleaner to return to the dock."""
        await self._send_command(
            "robotCleanerMovement", "setRobotCleanerMovement", ["homing"]
        )

    async def _send_command(
        self,
        capability: str,
        command: str,
        arguments: list | None = None,
    ) -> None:
        """Send a command to the device."""
        api = self.coordinator.api
        try:
            await api.send_device_command(
                self._device_id,
                capability,
                command,
                arguments or [],
            )
            # Request an immediate update
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to send command %s to device %s: %s",
                command,
                self._device_id,
                err,
            )
