"""Sensor platform for SmartThings Community Edition."""

import logging
from typing import Any, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfElectricPotential,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, DEVICE_VERSION, get_device_capabilities

_LOGGER = logging.getLogger(__name__)

# Sensor capability mappings
SENSOR_TYPES = {
    "temperatureMeasurement": {
        "name": "Temperature",
        "attribute": "temperature",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:thermometer",
    },
    "relativeHumidityMeasurement": {
        "name": "Humidity",
        "attribute": "humidity",
        "device_class": SensorDeviceClass.HUMIDITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
        "icon": "mdi:water-percent",
    },
    "illuminanceMeasurement": {
        "name": "Illuminance",
        "attribute": "illuminance",
        "device_class": SensorDeviceClass.ILLUMINANCE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "lx",
        "icon": "mdi:brightness-5",
    },
    "powerMeter": {
        "name": "Power",
        "attribute": "power",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:flash",
    },
    "energyMeter": {
        "name": "Energy",
        "attribute": "energy",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "icon": "mdi:lightning-bolt",
    },
    "battery": {
        "name": "Battery",
        "attribute": "battery",
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
        "icon": "mdi:battery",
    },
    "voltage": {
        "name": "Voltage",
        "attribute": "voltage",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
        "icon": "mdi:sine-wave",
    },
    # Appliance sensors
    "refrigerationSetpoint": {
        "name": "Refrigeration Setpoint",
        "attribute": "refrigerationSetpoint",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:fridge-outline",
    },
    "ovenSetpoint": {
        "name": "Oven Setpoint",
        "attribute": "ovenSetpoint",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:thermometer",
    },
    "washerOperatingState": {
        "name": "Washer State",
        "attribute": "machineState",
        "device_class": None,
        "state_class": None,
        "unit": None,
        "icon": "mdi:washing-machine",
    },
    "washerMode": {
        "name": "Washer Mode",
        "attribute": "washerMode",
        "device_class": None,
        "state_class": None,
        "unit": None,
        "icon": "mdi:washing-machine",
    },
    "dryerOperatingState": {
        "name": "Dryer State",
        "attribute": "machineState",
        "device_class": None,
        "state_class": None,
        "unit": None,
        "icon": "mdi:tumble-dryer",
    },
    "dryerMode": {
        "name": "Dryer Mode",
        "attribute": "dryerMode",
        "device_class": None,
        "state_class": None,
        "unit": None,
        "icon": "mdi:tumble-dryer",
    },
    "ovenOperatingState": {
        "name": "Oven State",
        "attribute": "machineState",
        "device_class": None,
        "state_class": None,
        "unit": None,
        "icon": "mdi:stove",
    },
    "ovenMode": {
        "name": "Oven Mode",
        "attribute": "ovenMode",
        "device_class": None,
        "state_class": None,
        "unit": None,
        "icon": "mdi:stove",
    },
    "dishwasherOperatingState": {
        "name": "Dishwasher State",
        "attribute": "machineState",
        "device_class": None,
        "state_class": None,
        "unit": None,
        "icon": "mdi:dishwasher",
    },
    "dishwasherMode": {
        "name": "Dishwasher Mode",
        "attribute": "dishwasherMode",
        "device_class": None,
        "state_class": None,
        "unit": None,
        "icon": "mdi:dishwasher",
    },
    "refrigeration": {
        "name": "Refrigeration Status",
        "attribute": "rapidFreezing,rapidCooling",  # Check multiple attributes
        "device_class": None,
        "state_class": None,
        "unit": None,
        "icon": "mdi:fridge",
    },
    "custom.runningTime": {
        "name": "Running Time",
        "attribute": "runningTime",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTime.MINUTES,
        "icon": "mdi:timer",
    },
    "custom.completionTime": {
        "name": "Completion Time",
        "attribute": "completionTime",
        "device_class": SensorDeviceClass.TIMESTAMP,
        "state_class": None,
        "unit": None,
        "icon": "mdi:clock-end",
    },
    "custom.runningCourse": {
        "name": "Running Course",
        "attribute": "course",
        "device_class": None,
        "state_class": None,
        "unit": None,
        "icon": "mdi:playlist-check",
    },
    "custom.error": {
        "name": "Error",
        "attribute": "error",
        "device_class": None,
        "state_class": None,
        "unit": None,
        "icon": "mdi:alert-circle",
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SmartThings sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities = []

    for device_id, device in coordinator.devices.items():
        # Get capabilities from the main component
        capability_ids = get_device_capabilities(device)
        
        # Create sensor for each supported capability
        for cap_id in capability_ids:
            if cap_id in SENSOR_TYPES:
                entities.append(
                    SmartThingsSensor(
                        coordinator,
                        device_id,
                        cap_id,
                        SENSOR_TYPES[cap_id],
                    )
                )

    async_add_entities(entities)


class SmartThingsSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator,
        device_id: str,
        capability: str,
        sensor_config: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._capability = capability
        self._attribute = sensor_config["attribute"]
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{capability}"
        self._attr_name = sensor_config["name"]
        self._attr_device_class = sensor_config.get("device_class")
        self._attr_state_class = sensor_config.get("state_class")
        self._attr_native_unit_of_measurement = sensor_config.get("unit")
        self._attr_icon = sensor_config.get("icon")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        device_status = device.get("status", {})
        main_status = device_status.get("main", {})
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
        
        # For Samsung appliances, prefer Micom firmware version and otnDUID model
        software_version = main_status.get("samsungce.softwareVersion", {})
        if software_version:
            versions = software_version.get("versions", {}).get("value", [])
            for ver in versions:
                if ver.get("description") == "Micom" and ver.get("swType") == "Firmware":
                    device_info["sw_version"] = ver.get("versionNumber")
                    break
        
        software_update = main_status.get("samsungce.softwareUpdate", {})
        if software_update:
            otn_duid = software_update.get("otnDUID", {}).get("value")
            if otn_duid:
                device_info["model"] = otn_duid
        
        return DeviceInfo(**device_info)

    @property
    def native_value(self) -> Optional[Any]:
        """Return the state of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        device_status = device.get("status", {})
        
        # Handle multiple attributes (comma-separated) for refrigeration
        attributes = [attr.strip() for attr in self._attribute.split(",")]
        
        # Try to find the capability in any component, not just "main"
        value = None
        for component_id, component_data in device_status.items():
            if self._capability in component_data:
                capability_data = component_data.get(self._capability, {})
                # Try each attribute in order
                for attr in attributes:
                    attr_value = capability_data.get(attr, {}).get("value")
                    if attr_value is not None:
                        value = attr_value
                        break
                if value is not None:
                    break
        
        if value is not None:
            # For numeric sensors, try to convert to float
            if self._attr_device_class in [
                SensorDeviceClass.TEMPERATURE,
                SensorDeviceClass.HUMIDITY,
                SensorDeviceClass.POWER,
                SensorDeviceClass.ENERGY,
                SensorDeviceClass.BATTERY,
                SensorDeviceClass.VOLTAGE,
                SensorDeviceClass.ILLUMINANCE,
            ]:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            # For non-numeric sensors (like refrigeration status), return the string value
            return str(value)
        
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None
