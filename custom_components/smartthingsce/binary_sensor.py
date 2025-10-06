"""Binary sensor platform for SmartThings Community Edition."""

import logging
from typing import Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, DEVICE_VERSION, get_device_capabilities

_LOGGER = logging.getLogger(__name__)

# Binary sensor capability mappings
BINARY_SENSOR_TYPES = {
    "contactSensor": {
        "name": "Contact",
        "attribute": "contact",
        "device_class": BinarySensorDeviceClass.DOOR,
        "on_state": "open",
        "icon": "mdi:door",
    },
    "motionSensor": {
        "name": "Motion",
        "attribute": "motion",
        "device_class": BinarySensorDeviceClass.MOTION,
        "on_state": "active",
        "icon": "mdi:motion-sensor",
    },
    "presenceSensor": {
        "name": "Presence",
        "attribute": "presence",
        "device_class": BinarySensorDeviceClass.PRESENCE,
        "on_state": "present",
        "icon": "mdi:account",
    },
    "waterSensor": {
        "name": "Water",
        "attribute": "water",
        "device_class": BinarySensorDeviceClass.MOISTURE,
        "on_state": "wet",
        "icon": "mdi:water",
    },
    "smokeDetector": {
        "name": "Smoke",
        "attribute": "smoke",
        "device_class": BinarySensorDeviceClass.SMOKE,
        "on_state": "detected",
        "icon": "mdi:smoke-detector",
    },
    "carbonMonoxideDetector": {
        "name": "Carbon Monoxide",
        "attribute": "carbonMonoxide",
        "device_class": BinarySensorDeviceClass.CO,
        "on_state": "detected",
        "icon": "mdi:smoke-detector-alert",
    },
    # Appliance binary sensors
    "washerOperatingState": {
        "name": "Washer Running",
        "attribute": "machineState",
        "device_class": BinarySensorDeviceClass.RUNNING,
        "on_state": "run",
        "icon": "mdi:washing-machine",
    },
    "dryerOperatingState": {
        "name": "Dryer Running",
        "attribute": "machineState",
        "device_class": BinarySensorDeviceClass.RUNNING,
        "on_state": "run",
        "icon": "mdi:tumble-dryer",
    },
    "ovenOperatingState": {
        "name": "Oven Running",
        "attribute": "machineState",
        "device_class": BinarySensorDeviceClass.RUNNING,
        "on_state": "run",
        "icon": "mdi:stove",
    },
    "dishwasherOperatingState": {
        "name": "Dishwasher Running",
        "attribute": "machineState",
        "device_class": BinarySensorDeviceClass.RUNNING,
        "on_state": "run",
        "icon": "mdi:dishwasher",
    },
    "custom.error": {
        "name": "Error",
        "attribute": "error",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "on_state": "detected",
        "icon": "mdi:alert-circle",
    },
    "samsungce.kidsLock": {
        "name": "Kids Lock",
        "attribute": "lockState",
        "device_class": BinarySensorDeviceClass.LOCK,
        "on_state": "locked",
        "icon": "mdi:lock-outline",
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SmartThings binary sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities = []

    for device_id, device in coordinator.devices.items():
        # Get capabilities from the main component
        capability_ids = get_device_capabilities(device)
        
        # Create binary sensor for each supported capability
        for cap_id in capability_ids:
            if cap_id in BINARY_SENSOR_TYPES:
                entities.append(
                    SmartThingsBinarySensor(
                        coordinator,
                        device_id,
                        cap_id,
                        BINARY_SENSOR_TYPES[cap_id],
                    )
                )

    async_add_entities(entities)


class SmartThingsBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a SmartThings binary sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator,
        device_id: str,
        capability: str,
        sensor_config: dict,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._capability = capability
        self._attribute = sensor_config["attribute"]
        self._on_state = sensor_config["on_state"]
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{capability}"
        self._attr_name = sensor_config["name"]
        self._attr_device_class = sensor_config.get("device_class")
        self._attr_icon = sensor_config.get("icon")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        ocf = device.get("ocf", {})
        
        device_info = {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": device.get("label", device.get("name", "Unknown")),
            "manufacturer": device.get("manufacturerName", "SmartThings"),
            "model": device.get("deviceTypeName", "Sensor"),
            "sw_version": DEVICE_VERSION,
        }
        
        # Add OCF device information if available
        if ocf:
            if "firmwareVersion" in ocf:
                device_info["sw_version"] = ocf["firmwareVersion"]
            if "hwVersion" in ocf:
                device_info["hw_version"] = ocf["hwVersion"]
            if "modelNumber" in ocf:
                device_info["model"] = ocf["modelNumber"]
        
        return DeviceInfo(**device_info)

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if the binary sensor is on."""
        device = self.coordinator.devices.get(self._device_id, {})
        device_status = device.get("status", {})
        
        # Try to find the capability in any component, not just "main"
        value = None
        for component_id, component_data in device_status.items():
            if self._capability in component_data:
                capability_data = component_data.get(self._capability, {})
                value = capability_data.get(self._attribute, {}).get("value")
                if value is not None:
                    break
        
        if value is not None:
            return value == self._on_state
        
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None
