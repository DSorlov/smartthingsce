"""Siren platform for SmartThings Community Edition."""

from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.siren import (
    SirenEntity,
    SirenEntityFeature,
    ATTR_TONE,
    ATTR_DURATION,
    ATTR_VOLUME_LEVEL,
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
    """Set up the SmartThings siren platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []
    for device_id, device in coordinator.devices.items():
        capability_ids = get_device_capabilities(device)

        # Check for siren capabilities
        if "alarm" in capability_ids:
            _LOGGER.info(
                "Creating alarm siren for device %s", device.get("label", device_id)
            )
            entities.append(SmartThingsAlarmSiren(coordinator, api, device_id))
        elif "tone" in capability_ids:
            _LOGGER.info(
                "Creating tone siren for device %s", device.get("label", device_id)
            )
            entities.append(SmartThingsToneSiren(coordinator, api, device_id))
        elif "chime" in capability_ids:
            _LOGGER.info(
                "Creating chime siren for device %s", device.get("label", device_id)
            )
            entities.append(SmartThingsChimeSiren(coordinator, api, device_id))

    async_add_entities(entities)


class SmartThingsAlarmSiren(CoordinatorEntity, SirenEntity):
    """Representation of a SmartThings alarm siren."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the siren."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_alarm_siren"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Alarm"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the siren."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("label", device.get("name", "Alarm"))

    @property
    def supported_features(self) -> SirenEntityFeature:
        """Return the list of supported features."""
        return SirenEntityFeature.TURN_ON | SirenEntityFeature.TURN_OFF

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if siren is on."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "alarm" in component_status:
                alarm_state = component_status["alarm"].get("alarm", {}).get("value")
                return alarm_state in ["siren", "strobe", "both"]

        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the siren on."""
        try:
            # Use "both" as default (siren + strobe)
            await self._api.send_device_command(
                self._device_id,
                "alarm",
                "both",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on alarm siren %s: %s", self._device_id, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the siren off."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "alarm",
                "off",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off alarm siren %s: %s", self._device_id, err)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:alarm-light"


class SmartThingsToneSiren(CoordinatorEntity, SirenEntity):
    """Representation of a SmartThings tone siren."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the siren."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_tone_siren"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Tone"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the siren."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("label", device.get("name", "Tone"))

    @property
    def supported_features(self) -> SirenEntityFeature:
        """Return the list of supported features."""
        features = SirenEntityFeature.TURN_ON | SirenEntityFeature.TURN_OFF

        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        # Check if device supports tones
        for component_id, component_status in status.items():
            if "tone" in component_status:
                available_tones = (
                    component_status.get("tone", {})
                    .get("availableTones", {})
                    .get("value", [])
                )
                if available_tones:
                    features |= SirenEntityFeature.TONES
                break

        return features

    @property
    def available_tones(self) -> Optional[list[str | int]]:
        """Return a list of available tones."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "tone" in component_status:
                tones = (
                    component_status["tone"].get("availableTones", {}).get("value", [])
                )
                return tones if tones else None

        return None

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if siren is on."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "tone" in component_status:
                tone_state = component_status["tone"].get("tone", {}).get("value")
                return tone_state is not None and tone_state != "off"

        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the siren on."""
        try:
            tone = kwargs.get(ATTR_TONE)
            if tone is None:
                # Use first available tone as default
                available_tones = self.available_tones
                if available_tones:
                    tone = available_tones[0]
                else:
                    tone = 1  # Default tone

            await self._api.send_device_command(
                self._device_id,
                "tone",
                "beep",
                [tone],
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on tone siren %s: %s", self._device_id, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the siren off."""
        try:
            # Most tone devices don't have explicit off, but try anyway
            await self._api.send_device_command(
                self._device_id,
                "tone",
                "off",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.debug(
                "Tone siren %s may not support off command: %s", self._device_id, err
            )

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:volume-high"


class SmartThingsChimeSiren(CoordinatorEntity, SirenEntity):
    """Representation of a SmartThings chime siren."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the siren."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_chime_siren"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Chime"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the siren."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("label", device.get("name", "Chime"))

    @property
    def supported_features(self) -> SirenEntityFeature:
        """Return the list of supported features."""
        return SirenEntityFeature.TURN_ON | SirenEntityFeature.TURN_OFF

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if siren is on."""
        # Chimes typically don't have persistent state
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the siren on (play chime)."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "chime",
                "chime",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to play chime %s: %s", self._device_id, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the siren off (not applicable for chimes)."""
        # Chimes typically can't be turned off as they play briefly
        _LOGGER.debug("Chime %s cannot be turned off", self._device_id)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:bell-ring"
