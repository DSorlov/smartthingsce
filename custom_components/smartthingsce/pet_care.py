"""Pet Care platform for SmartThings Community Edition."""
from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import PERCENTAGE, UnitOfMass, UnitOfVolume
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
    """Set up the SmartThings pet care platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []
    for device_id, device in coordinator.devices.items():
        capability_ids = get_device_capabilities(device)
        
        # Pet Feeder devices
        if "petFeederOperatingState" in capability_ids:
            device_label = device.get("label", device_id)
            
            # Operating state sensor
            _LOGGER.info("Creating pet feeder operating state sensor for device %s", device_label)
            entities.append(SmartThingsPetFeederOperatingState(coordinator, api, device_id))
            
            # Food level sensor if available
            if "petFeederFoodLevel" in capability_ids:
                _LOGGER.info("Creating pet feeder food level sensor for device %s", device_label)
                entities.append(SmartThingsPetFeederFoodLevel(coordinator, api, device_id))
                
            # Feeding schedule sensor if available
            if "petFeederSchedule" in capability_ids:
                _LOGGER.info("Creating pet feeder schedule sensor for device %s", device_label)
                entities.append(SmartThingsPetFeederSchedule(coordinator, api, device_id))
                
            # Feed control switch if available
            if "petFeederFeed" in capability_ids:
                _LOGGER.info("Creating pet feeder feed control for device %s", device_label)
                entities.append(SmartThingsPetFeederFeedControl(coordinator, api, device_id))

    async_add_entities(entities)


class SmartThingsPetFeederOperatingState(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Pet Feeder Operating State sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_pet_feeder_state"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Pet Feeder"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Operating State"

    @property
    def native_value(self) -> Optional[str]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})
        
        for component_id, component_status in status.items():
            if "petFeederOperatingState" in component_status:
                state = component_status["petFeederOperatingState"].get("operatingState", {}).get("value")
                return state
        
        return None

    @property
    def options(self) -> list[str]:
        """Return the list of available options."""
        return ["idle", "feeding", "dispensing", "jammed", "empty", "error"]

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    @property
    def icon(self) -> str:
        """Return the icon."""
        state = self.native_value
        if state == "feeding":
            return "mdi:bowl"
        elif state == "jammed":
            return "mdi:alert-circle"
        elif state == "empty":
            return "mdi:bowl-outline"
        elif state == "error":
            return "mdi:alert"
        return "mdi:food-variant"


class SmartThingsPetFeederFoodLevel(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Pet Feeder Food Level sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_pet_feeder_food_level"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Pet Feeder"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Food Level"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})
        
        for component_id, component_status in status.items():
            if "petFeederFoodLevel" in component_status:
                level = component_status["petFeederFoodLevel"].get("foodLevel", {}).get("value")
                if level is not None:
                    try:
                        return float(level)
                    except (ValueError, TypeError):
                        pass
        
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    @property
    def icon(self) -> str:
        """Return the icon."""
        level = self.native_value
        if level is not None:
            if level <= 10:
                return "mdi:food-variant-off"
            elif level <= 30:
                return "mdi:food-variant"
            else:
                return "mdi:food"
        return "mdi:food-variant"


class SmartThingsPetFeederSchedule(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Pet Feeder Schedule sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_pet_feeder_schedule"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Pet Feeder"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Feeding Schedule"

    @property
    def native_value(self) -> Optional[str]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})
        
        for component_id, component_status in status.items():
            if "petFeederSchedule" in component_status:
                schedule = component_status["petFeederSchedule"].get("schedule", {}).get("value")
                if isinstance(schedule, dict):
                    # Format schedule info
                    next_feeding = schedule.get("nextFeeding")
                    if next_feeding:
                        return f"Next: {next_feeding}"
                elif isinstance(schedule, str):
                    return schedule
        
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})
        attributes = {}
        
        for component_id, component_status in status.items():
            if "petFeederSchedule" in component_status:
                schedule_data = component_status["petFeederSchedule"]
                
                if "schedule" in schedule_data:
                    schedule = schedule_data["schedule"].get("value", {})
                    if isinstance(schedule, dict):
                        for key, value in schedule.items():
                            attributes[f"schedule_{key}"] = value
                
                break
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:calendar-clock"


class SmartThingsPetFeederFeedControl(CoordinatorEntity, SwitchEntity):
    """Representation of a SmartThings Pet Feeder Feed Control switch."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_pet_feeder_feed"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Pet Feeder"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return "Feed Now"

    @property
    def is_on(self) -> bool:
        """Return true if currently feeding."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})
        
        for component_id, component_status in status.items():
            if "petFeederOperatingState" in component_status:
                state = component_status["petFeederOperatingState"].get("operatingState", {}).get("value")
                return state in ["feeding", "dispensing"]
        
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start feeding."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "petFeederFeed",
                "feed",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to start feeding %s: %s", self._device_id, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop feeding."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "petFeederFeed",
                "stop",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to stop feeding %s: %s", self._device_id, err)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:food-variant" if not self.is_on else "mdi:bowl"