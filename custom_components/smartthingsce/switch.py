"""Switch platform for SmartThings Community Edition."""

import logging
from typing import Any, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DEVICE_AUTHOR, DEVICE_VERSION, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SmartThings switches."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []

    for device_id, device in coordinator.devices.items():
        # Get capabilities from the main component
        capability_ids = get_device_capabilities(device)

        # Check if device has switch capability
        if "switch" in capability_ids:
            entities.append(SmartThingsSwitch(coordinator, api, device_id))

        # Check for Samsung refrigeration controls - only add if NOT disabled
        # Disabled capabilities are marked in custom.disabledCapabilities in main component
        status = device.get("status", {})
        main_status = status.get("main", {})
        disabled_capabilities = (
            main_status.get("custom.disabledCapabilities", {})
            .get("disabledCapabilities", {})
            .get("value", [])
        )

        if (
            "samsungce.powerCool" in capability_ids
            and "samsungce.powerCool" not in disabled_capabilities
        ):
            _LOGGER.info(
                "Creating Power Cool switch for device %s",
                device.get("label", device_id),
            )
            entities.append(SmartThingsPowerCoolSwitch(coordinator, api, device_id))
        elif "samsungce.powerCool" in capability_ids:
            _LOGGER.debug(
                "Skipping Power Cool switch for device %s - disabled",
                device.get("label", device_id),
            )

        if (
            "samsungce.powerFreeze" in capability_ids
            and "samsungce.powerFreeze" not in disabled_capabilities
        ):
            _LOGGER.info(
                "Creating Power Freeze switch for device %s",
                device.get("label", device_id),
            )
            entities.append(SmartThingsPowerFreezeSwitch(coordinator, api, device_id))
        elif "samsungce.powerFreeze" in capability_ids:
            _LOGGER.debug(
                "Skipping Power Freeze switch for device %s - disabled",
                device.get("label", device_id),
            )

    async_add_entities(entities)


class SmartThingsSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a SmartThings switch."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_switch"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Switch"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("label", device.get("name", "Switch"))

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if switch is on."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {}).get("main", {}).get("switch", {})
        switch_state = status.get("switch", {}).get("value")
        return switch_state == "on"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "switch",
                "on",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on switch %s: %s", self._device_id, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "switch",
                "off",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off switch %s: %s", self._device_id, err)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:toggle-switch"


def get_device_capabilities(device: dict) -> list:
    """Get all capabilities from a device."""
    capabilities = []
    for component in device.get("components", []):
        for cap in component.get("capabilities", []):
            capabilities.append(cap.get("id"))
    return capabilities


class SmartThingsPowerCoolSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a SmartThings Power Cool switch."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_power_cool"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})

        # Get firmware version from samsungce.softwareVersion
        status = device.get("status", {})
        firmware_version = None
        for component_id, component_status in status.items():
            if "samsungce.softwareVersion" in component_status:
                versions = (
                    component_status["samsungce.softwareVersion"]
                    .get("versions", {})
                    .get("value", [])
                )
                for version in versions:
                    if version.get("description") == "Micom":
                        firmware_version = version.get("versionNumber")
                        break
                if firmware_version:
                    break

        # Get model from samsungce.softwareUpdate
        model = None
        for component_id, component_status in status.items():
            if "samsungce.softwareUpdate" in component_status:
                model = (
                    component_status["samsungce.softwareUpdate"]
                    .get("otnDUID", {})
                    .get("value")
                )
                if model:
                    break

        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=model or device.get("deviceTypeName", "Refrigerator"),
            sw_version=firmware_version or DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return "Power Cool"

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if power cool is on."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        # Check all components for powerCool capability
        for component_id, component_status in status.items():
            if "samsungce.powerCool" in component_status:
                activated = (
                    component_status["samsungce.powerCool"]
                    .get("activated", {})
                    .get("value")
                )
                # None means capability is disabled on this device - this shouldn't happen if setup is correct
                # but handle it gracefully
                if activated is None:
                    return False
                return activated is True or activated == "on"

        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn power cool on."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "samsungce.powerCool",
                "setActivate",
                [True],
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on power cool %s: %s", self._device_id, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn power cool off."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "samsungce.powerCool",
                "setActivate",
                [False],
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off power cool %s: %s", self._device_id, err)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:snowflake-alert"


class SmartThingsPowerFreezeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a SmartThings Power Freeze switch."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_power_freeze"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})

        # Get firmware version from samsungce.softwareVersion
        status = device.get("status", {})
        firmware_version = None
        for component_id, component_status in status.items():
            if "samsungce.softwareVersion" in component_status:
                versions = (
                    component_status["samsungce.softwareVersion"]
                    .get("versions", {})
                    .get("value", [])
                )
                for version in versions:
                    if version.get("description") == "Micom":
                        firmware_version = version.get("versionNumber")
                        break
                if firmware_version:
                    break

        # Get model from samsungce.softwareUpdate
        model = None
        for component_id, component_status in status.items():
            if "samsungce.softwareUpdate" in component_status:
                model = (
                    component_status["samsungce.softwareUpdate"]
                    .get("otnDUID", {})
                    .get("value")
                )
                if model:
                    break

        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=model or device.get("deviceTypeName", "Refrigerator"),
            sw_version=firmware_version or DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return "Power Freeze"

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if power freeze is on."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        # Check all components for powerFreeze capability
        for component_id, component_status in status.items():
            if "samsungce.powerFreeze" in component_status:
                activated = (
                    component_status["samsungce.powerFreeze"]
                    .get("activated", {})
                    .get("value")
                )
                # None means capability is disabled on this device - this shouldn't happen if setup is correct
                # but handle it gracefully
                if activated is None:
                    return False
                return activated is True or activated == "on"

        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn power freeze on."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "samsungce.powerFreeze",
                "setActivate",
                [True],
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on power freeze %s: %s", self._device_id, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn power freeze off."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "samsungce.powerFreeze",
                "setActivate",
                [False],
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to turn off power freeze %s: %s", self._device_id, err
            )

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:snowflake"
