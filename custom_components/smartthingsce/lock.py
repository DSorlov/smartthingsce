"""Lock platform for SmartThings Community Edition."""

import logging
from typing import Any, Optional

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DEVICE_VERSION, DOMAIN, get_device_capabilities

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SmartThings locks."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []

    for device_id, device in coordinator.devices.items():
        # Get capabilities - SmartThings API returns them as a list at device level
        capabilities = device.get("capabilities", [])
        capability_ids = [
            cap.get("id") if isinstance(cap, dict) else cap for cap in capabilities
        ]

        # Check if device has lock capability
        if "lock" in capability_ids:
            entities.append(SmartThingsLock(coordinator, api, device_id))

    async_add_entities(entities)


class SmartThingsLock(CoordinatorEntity, LockEntity):
    """Representation of a SmartThings lock."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the lock."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_lock"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Lock"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the lock."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("label", device.get("name", "Lock"))

    @property
    def is_locked(self) -> Optional[bool]:
        """Return true if lock is locked."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {}).get("main", {}).get("lock", {})
        lock_state = status.get("lock", {}).get("value")
        return lock_state == "locked"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "lock",
                "lock",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to lock %s: %s", self._device_id, err)

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "lock",
                "unlock",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to unlock %s: %s", self._device_id, err)
