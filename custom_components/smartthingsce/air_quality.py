"""Air Quality sensor platform for SmartThings Community Edition."""

from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DEVICE_VERSION, DOMAIN, get_device_capabilities

_LOGGER = logging.getLogger(__name__)

# Air Quality Index mapping
AIR_QUALITY_INDEX_MAP = {
    1: "Good",
    2: "Moderate",
    3: "Unhealthy for Sensitive Groups",
    4: "Unhealthy",
    5: "Very Unhealthy",
    6: "Hazardous",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SmartThings air quality sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []
    for device_id, device in coordinator.devices.items():
        capability_ids = get_device_capabilities(device)

        # Air Quality Detector
        if "airQualityDetector" in capability_ids:
            _LOGGER.info(
                "Creating air quality index sensor for device %s",
                device.get("label", device_id),
            )
            entities.append(SmartThingsAirQualityIndex(coordinator, api, device_id))

        # Dust Sensor (PM2.5/PM10)
        if "dustSensor" in capability_ids:
            _LOGGER.info(
                "Creating dust sensor for device %s", device.get("label", device_id)
            )
            entities.append(SmartThingsDustSensor(coordinator, api, device_id))

        # TVOC Measurement (Total Volatile Organic Compounds)
        if "tvocMeasurement" in capability_ids:
            _LOGGER.info(
                "Creating TVOC sensor for device %s", device.get("label", device_id)
            )
            entities.append(SmartThingsTVOCSensor(coordinator, api, device_id))

        # Formaldehyde Measurement
        if "formaldehydeMeasurement" in capability_ids:
            _LOGGER.info(
                "Creating formaldehyde sensor for device %s",
                device.get("label", device_id),
            )
            entities.append(SmartThingsFormaldehydeSensor(coordinator, api, device_id))

        # Air Quality Health Concern
        if "airQualityHealthConcern" in capability_ids:
            _LOGGER.info(
                "Creating air quality health concern sensor for device %s",
                device.get("label", device_id),
            )
            entities.append(
                SmartThingsAirQualityHealthConcern(coordinator, api, device_id)
            )

    async_add_entities(entities)


class SmartThingsAirQualityIndex(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Air Quality Index sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.AQI
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_air_quality_index"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Air Quality Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Air Quality Index"

    @property
    def native_value(self) -> Optional[int]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "airQualityDetector" in component_status:
                aqi = (
                    component_status["airQualityDetector"]
                    .get("airQuality", {})
                    .get("value")
                )
                if aqi is not None:
                    try:
                        return int(aqi)
                    except (ValueError, TypeError):
                        pass

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        aqi_value = self.native_value
        attributes = {}

        if aqi_value is not None:
            attributes["aqi_description"] = AIR_QUALITY_INDEX_MAP.get(
                aqi_value, "Unknown"
            )

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:air-filter"


class SmartThingsDustSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Dust/Particulate Matter sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.PM25
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_dust_sensor"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Air Quality Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Particulate Matter"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "dustSensor" in component_status:
                # Try PM2.5 first, then PM10, then generic dust level
                dust_data = component_status["dustSensor"]

                if "fineDustLevel" in dust_data:
                    pm25 = dust_data["fineDustLevel"].get("value")
                    if pm25 is not None:
                        try:
                            return float(pm25)
                        except (ValueError, TypeError):
                            pass

                if "dustLevel" in dust_data:
                    dust = dust_data["dustLevel"].get("value")
                    if dust is not None:
                        try:
                            return float(dust)
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
            if "dustSensor" in component_status:
                dust_data = component_status["dustSensor"]

                # Add PM10 if available
                if "dustLevel" in dust_data:
                    pm10 = dust_data["dustLevel"].get("value")
                    if pm10 is not None:
                        attributes["pm10"] = pm10

                # Add fine dust level (PM2.5) separately if we're showing PM10 as main
                if "fineDustLevel" in dust_data:
                    pm25 = dust_data["fineDustLevel"].get("value")
                    if pm25 is not None and self.name != "PM2.5":
                        attributes["pm25"] = pm25

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
        return "mdi:blur"


class SmartThingsTVOCSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings TVOC sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_tvoc_sensor"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Air Quality Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "TVOC"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "tvocMeasurement" in component_status:
                tvoc = (
                    component_status["tvocMeasurement"]
                    .get("tvocLevel", {})
                    .get("value")
                )
                if tvoc is not None:
                    try:
                        return float(tvoc)
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
        return "mdi:chemical-weapon"


class SmartThingsFormaldehydeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Formaldehyde sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_formaldehyde_sensor"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Air Quality Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Formaldehyde"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "formaldehydeMeasurement" in component_status:
                formaldehyde = (
                    component_status["formaldehydeMeasurement"]
                    .get("formaldehydeLevel", {})
                    .get("value")
                )
                if formaldehyde is not None:
                    try:
                        return float(formaldehyde)
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
        return "mdi:molecule"


class SmartThingsAirQualityHealthConcern(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Air Quality Health Concern sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_air_quality_health_concern"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Air Quality Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Air Quality Health Concern"

    @property
    def native_value(self) -> Optional[str]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "airQualityHealthConcern" in component_status:
                concern = (
                    component_status["airQualityHealthConcern"]
                    .get("airQualityHealthConcern", {})
                    .get("value")
                )
                return concern

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    @property
    def icon(self) -> str:
        """Return the icon."""
        concern_level = self.native_value
        if concern_level:
            concern_lower = concern_level.lower()
            if "good" in concern_lower:
                return "mdi:emoticon-happy"
            elif "moderate" in concern_lower:
                return "mdi:emoticon-neutral"
            elif "unhealthy" in concern_lower:
                return "mdi:emoticon-sad"
            elif "hazardous" in concern_lower:
                return "mdi:emoticon-dead"

        return "mdi:air-filter"
