"""Energy Monitor sensor platform for SmartThings Community Edition."""

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
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)
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
    """Set up the SmartThings energy monitor sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []
    for device_id, device in coordinator.devices.items():
        capability_ids = get_device_capabilities(device)

        # Check for energy monitoring capabilities
        has_energy_capabilities = any(
            cap in capability_ids
            for cap in [
                "energyMeter",
                "powerMeter",
                "voltageMeasurement",
                "currentMeasurement",
            ]
        )

        if has_energy_capabilities:
            device_label = device.get("label", device_id)

            # Energy Meter (cumulative energy consumption)
            if "energyMeter" in capability_ids:
                _LOGGER.info("Creating energy meter sensor for device %s", device_label)
                entities.append(SmartThingsEnergyMeter(coordinator, api, device_id))

            # Power Meter (instantaneous power consumption)
            if "powerMeter" in capability_ids:
                _LOGGER.info("Creating power meter sensor for device %s", device_label)
                entities.append(SmartThingsPowerMeter(coordinator, api, device_id))

            # Voltage Measurement
            if "voltageMeasurement" in capability_ids:
                _LOGGER.info("Creating voltage sensor for device %s", device_label)
                entities.append(SmartThingsVoltageSensor(coordinator, api, device_id))

            # Current Measurement
            if "currentMeasurement" in capability_ids:
                _LOGGER.info("Creating current sensor for device %s", device_label)
                entities.append(SmartThingsCurrentSensor(coordinator, api, device_id))

    async_add_entities(entities)


class SmartThingsEnergyMeter(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Energy Meter sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_energy_meter"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Energy Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Energy"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "energyMeter" in component_status:
                energy = component_status["energyMeter"].get("energy", {}).get("value")
                if energy is not None:
                    try:
                        # SmartThings typically reports in Wh, convert to kWh
                        return float(energy) / 1000.0
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
            if "energyMeter" in component_status:
                energy_data = component_status["energyMeter"]

                # Add raw energy value in Wh
                if "energy" in energy_data:
                    raw_energy = energy_data["energy"].get("value")
                    if raw_energy is not None:
                        attributes["energy_wh"] = raw_energy

                # Add energy meter delta if available
                if "deltaEnergy" in energy_data:
                    delta = energy_data["deltaEnergy"].get("value")
                    if delta is not None:
                        attributes["delta_energy_wh"] = delta

                # Add any additional energy properties
                for key, value_dict in energy_data.items():
                    if key not in ["energy", "deltaEnergy"] and isinstance(
                        value_dict, dict
                    ):
                        if "value" in value_dict:
                            attributes[f"energy_{key}"] = value_dict["value"]

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
        return "mdi:lightning-bolt"


class SmartThingsPowerMeter(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Power Meter sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_power_meter"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Energy Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Power"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "powerMeter" in component_status:
                power = component_status["powerMeter"].get("power", {}).get("value")
                if power is not None:
                    try:
                        return float(power)
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
            if "powerMeter" in component_status:
                power_data = component_status["powerMeter"]

                # Add power consumption tier info if available
                if "powerConsumptionReport" in power_data:
                    report = power_data["powerConsumptionReport"].get("value", {})
                    if isinstance(report, dict):
                        for key, value in report.items():
                            attributes[f"power_{key}"] = value

                # Add any additional power properties
                for key, value_dict in power_data.items():
                    if key not in ["power", "powerConsumptionReport"] and isinstance(
                        value_dict, dict
                    ):
                        if "value" in value_dict:
                            attributes[f"power_{key}"] = value_dict["value"]

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
        return "mdi:flash"


class SmartThingsVoltageSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Voltage sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_voltage"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Energy Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Voltage"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "voltageMeasurement" in component_status:
                voltage = (
                    component_status["voltageMeasurement"]
                    .get("voltage", {})
                    .get("value")
                )
                if voltage is not None:
                    try:
                        return float(voltage)
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
        return "mdi:sine-wave"


class SmartThingsCurrentSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Current sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_current"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Energy Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Current"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "currentMeasurement" in component_status:
                current = (
                    component_status["currentMeasurement"]
                    .get("current", {})
                    .get("value")
                )
                if current is not None:
                    try:
                        return float(current)
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
        return "mdi:current-ac"
