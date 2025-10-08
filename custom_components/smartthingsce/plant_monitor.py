"""Plant Monitor platform for SmartThings Community Edition."""

from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfIlluminance,
    UnitOfTemperature,
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
    """Set up the SmartThings plant monitor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []
    for device_id, device in coordinator.devices.items():
        capability_ids = get_device_capabilities(device)

        # Plant Monitor devices - check for soil moisture or plant-specific capabilities
        is_plant_monitor = any(
            cap in capability_ids
            for cap in ["soilMoisture", "plantMoisture", "plantHealth", "plantNutrient"]
        )

        # Also check device type/name for plant monitors
        device_type = device.get("deviceTypeName", "").lower()
        device_label = device.get("label", "").lower()
        if any(
            keyword in device_type or keyword in device_label
            for keyword in ["plant", "soil", "garden", "moisture"]
        ):
            is_plant_monitor = True

        if is_plant_monitor:
            device_label = device.get("label", device_id)

            # Soil Moisture sensor
            if "soilMoisture" in capability_ids:
                _LOGGER.info(
                    "Creating soil moisture sensor for device %s", device_label
                )
                entities.append(SmartThingsSoilMoisture(coordinator, api, device_id))

            # Alternative: plantMoisture capability
            elif "plantMoisture" in capability_ids:
                _LOGGER.info(
                    "Creating plant moisture sensor for device %s", device_label
                )
                entities.append(SmartThingsPlantMoisture(coordinator, api, device_id))

            # Plant Health sensor
            if "plantHealth" in capability_ids:
                _LOGGER.info("Creating plant health sensor for device %s", device_label)
                entities.append(SmartThingsPlantHealth(coordinator, api, device_id))

            # Plant Nutrient sensor
            if "plantNutrient" in capability_ids:
                _LOGGER.info(
                    "Creating plant nutrient sensor for device %s", device_label
                )
                entities.append(SmartThingsPlantNutrient(coordinator, api, device_id))

            # Temperature sensor (for plant monitors)
            if "temperatureMeasurement" in capability_ids:
                _LOGGER.info(
                    "Creating plant temperature sensor for device %s", device_label
                )
                entities.append(
                    SmartThingsPlantTemperature(coordinator, api, device_id)
                )

            # Light sensor (for plant monitors)
            if "illuminanceMeasurement" in capability_ids:
                _LOGGER.info("Creating plant light sensor for device %s", device_label)
                entities.append(SmartThingsPlantLight(coordinator, api, device_id))

    async_add_entities(entities)


class SmartThingsSoilMoisture(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Soil Moisture sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.MOISTURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_soil_moisture"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Plant Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Soil Moisture"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "soilMoisture" in component_status:
                moisture = (
                    component_status["soilMoisture"]
                    .get("soilMoisture", {})
                    .get("value")
                )
                if moisture is not None:
                    try:
                        return float(moisture)
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
        moisture = self.native_value
        if moisture is not None:
            if moisture <= 20:
                return "mdi:water-outline"
            elif moisture <= 40:
                return "mdi:water-percent"
            else:
                return "mdi:water"
        return "mdi:water-percent"


class SmartThingsPlantMoisture(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Plant Moisture sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.MOISTURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_plant_moisture"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Plant Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Plant Moisture"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "plantMoisture" in component_status:
                moisture = (
                    component_status["plantMoisture"]
                    .get("plantMoisture", {})
                    .get("value")
                )
                if moisture is not None:
                    try:
                        return float(moisture)
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
        return "mdi:sprout"


class SmartThingsPlantHealth(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Plant Health sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_plant_health"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Plant Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Plant Health"

    @property
    def native_value(self) -> Optional[str]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "plantHealth" in component_status:
                health = (
                    component_status["plantHealth"].get("plantHealth", {}).get("value")
                )
                return health

        return None

    @property
    def options(self) -> list[str]:
        """Return the list of available options."""
        return ["excellent", "good", "fair", "poor", "critical"]

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    @property
    def icon(self) -> str:
        """Return the icon."""
        health = self.native_value
        if health:
            health_lower = health.lower()
            if health_lower in ["excellent", "good"]:
                return "mdi:leaf"
            elif health_lower == "fair":
                return "mdi:leaf-maple"
            elif health_lower == "poor":
                return "mdi:tree"
            elif health_lower == "critical":
                return "mdi:alert-circle"
        return "mdi:sprout"


class SmartThingsPlantNutrient(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Plant Nutrient sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_plant_nutrient"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Plant Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Plant Nutrient Level"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "plantNutrient" in component_status:
                nutrient = (
                    component_status["plantNutrient"]
                    .get("nutrientLevel", {})
                    .get("value")
                )
                if nutrient is not None:
                    try:
                        return float(nutrient)
                    except (ValueError, TypeError):
                        pass

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})
        attributes = {}

        for component_id, component_status in status.items():
            if "plantNutrient" in component_status:
                nutrient_data = component_status["plantNutrient"]

                # Add detailed nutrient information
                for key, value_dict in nutrient_data.items():
                    if isinstance(value_dict, dict) and "value" in value_dict:
                        if key != "nutrientLevel":
                            attributes[f"nutrient_{key}"] = value_dict["value"]

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
        return "mdi:nutrition"


class SmartThingsPlantTemperature(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Plant Monitor Temperature sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_plant_temperature"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Plant Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Temperature"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "temperatureMeasurement" in component_status:
                temp = (
                    component_status["temperatureMeasurement"]
                    .get("temperature", {})
                    .get("value")
                )
                if temp is not None:
                    try:
                        return float(temp)
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
        return "mdi:thermometer"


class SmartThingsPlantLight(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Plant Monitor Light sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.ILLUMINANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfIlluminance.LUX

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_plant_light"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Plant Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Light Level"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "illuminanceMeasurement" in component_status:
                illuminance = (
                    component_status["illuminanceMeasurement"]
                    .get("illuminance", {})
                    .get("value")
                )
                if illuminance is not None:
                    try:
                        return float(illuminance)
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
        return "mdi:brightness-6"
