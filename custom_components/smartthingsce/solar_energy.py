"""Solar Energy platform for SmartThings Community Edition."""

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
    PERCENTAGE,
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
    """Set up the SmartThings solar energy platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []
    for device_id, device in coordinator.devices.items():
        capability_ids = get_device_capabilities(device)

        # Solar/renewable energy devices - check for power source or solar-specific capabilities
        is_solar_device = any(
            cap in capability_ids
            for cap in ["powerSource", "solarPanel", "inverter", "batteryLevel"]
        )

        # Also check device type/name for solar equipment
        device_type = device.get("deviceTypeName", "").lower()
        device_label = device.get("label", "").lower()
        if any(
            keyword in device_type or keyword in device_label
            for keyword in ["solar", "inverter", "panel", "renewable", "generator"]
        ):
            is_solar_device = True

        if is_solar_device:
            device_label = device.get("label", device_id)

            # Power Source (solar generation)
            if "powerSource" in capability_ids:
                _LOGGER.info(
                    "Creating solar power source sensor for device %s", device_label
                )
                entities.append(
                    SmartThingsSolarPowerSource(coordinator, api, device_id)
                )

            # Solar Panel specific sensors
            if "solarPanel" in capability_ids:
                _LOGGER.info("Creating solar panel sensors for device %s", device_label)
                entities.append(SmartThingsSolarPanelPower(coordinator, api, device_id))
                entities.append(
                    SmartThingsSolarPanelEnergy(coordinator, api, device_id)
                )

            # Inverter sensors
            if "inverter" in capability_ids:
                _LOGGER.info(
                    "Creating solar inverter sensors for device %s", device_label
                )
                entities.append(
                    SmartThingsSolarInverterStatus(coordinator, api, device_id)
                )
                entities.append(
                    SmartThingsSolarInverterEfficiency(coordinator, api, device_id)
                )

            # Battery storage (for solar + storage systems)
            if "batteryLevel" in capability_ids:
                _LOGGER.info(
                    "Creating solar battery storage sensor for device %s", device_label
                )
                entities.append(
                    SmartThingsSolarBatteryLevel(coordinator, api, device_id)
                )

            # Enhanced energy monitoring for solar systems
            if "energyMeter" in capability_ids:
                _LOGGER.info(
                    "Creating solar energy production sensor for device %s",
                    device_label,
                )
                entities.append(
                    SmartThingsSolarEnergyProduction(coordinator, api, device_id)
                )

    async_add_entities(entities)


class SmartThingsSolarPowerSource(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Solar Power Source sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_solar_power_source"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Solar System"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Power Source"

    @property
    def native_value(self) -> Optional[str]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "powerSource" in component_status:
                source = (
                    component_status["powerSource"].get("powerSource", {}).get("value")
                )
                return source

        return None

    @property
    def options(self) -> list[str]:
        """Return the list of available options."""
        return ["solar", "battery", "grid", "generator", "unknown"]

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    @property
    def icon(self) -> str:
        """Return the icon."""
        source = self.native_value
        if source:
            source_lower = source.lower()
            if "solar" in source_lower:
                return "mdi:solar-panel"
            elif "battery" in source_lower:
                return "mdi:battery"
            elif "grid" in source_lower:
                return "mdi:transmission-tower"
            elif "generator" in source_lower:
                return "mdi:engine"
        return "mdi:lightning-bolt"


class SmartThingsSolarPanelPower(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Solar Panel Power sensor."""

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
        self._attr_unique_id = f"{DOMAIN}_{device_id}_solar_panel_power"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Solar Panel"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Solar Power Generation"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "solarPanel" in component_status:
                power = (
                    component_status["solarPanel"]
                    .get("powerGeneration", {})
                    .get("value")
                )
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
            if "solarPanel" in component_status:
                solar_data = component_status["solarPanel"]

                # Add solar panel specific attributes
                for key, value_dict in solar_data.items():
                    if isinstance(value_dict, dict) and "value" in value_dict:
                        if key != "powerGeneration":
                            attributes[f"solar_{key}"] = value_dict["value"]

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
        return "mdi:solar-panel-large"


class SmartThingsSolarPanelEnergy(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Solar Panel Energy sensor."""

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
        self._attr_unique_id = f"{DOMAIN}_{device_id}_solar_panel_energy"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Solar Panel"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Solar Energy Generated"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "solarPanel" in component_status:
                energy = (
                    component_status["solarPanel"]
                    .get("energyGeneration", {})
                    .get("value")
                )
                if energy is not None:
                    try:
                        # Convert Wh to kWh
                        return float(energy) / 1000.0
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
        return "mdi:solar-power"


class SmartThingsSolarInverterStatus(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Solar Inverter Status sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_solar_inverter_status"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Solar Inverter"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Inverter Status"

    @property
    def native_value(self) -> Optional[str]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "inverter" in component_status:
                inverter_status = (
                    component_status["inverter"].get("inverterStatus", {}).get("value")
                )
                return inverter_status

        return None

    @property
    def options(self) -> list[str]:
        """Return the list of available options."""
        return ["operating", "fault", "standby", "shutdown", "starting", "mppt"]

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    @property
    def icon(self) -> str:
        """Return the icon."""
        status = self.native_value
        if status:
            status_lower = status.lower()
            if "operating" in status_lower or "mppt" in status_lower:
                return "mdi:flash"
            elif "fault" in status_lower:
                return "mdi:alert-circle"
            elif "standby" in status_lower or "shutdown" in status_lower:
                return "mdi:pause-circle"
            elif "starting" in status_lower:
                return "mdi:play-circle"
        return "mdi:power-plug"


class SmartThingsSolarInverterEfficiency(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Solar Inverter Efficiency sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_solar_inverter_efficiency"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Solar Inverter"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Inverter Efficiency"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "inverter" in component_status:
                efficiency = (
                    component_status["inverter"].get("efficiency", {}).get("value")
                )
                if efficiency is not None:
                    try:
                        return float(efficiency)
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
        return "mdi:speedometer"


class SmartThingsSolarBatteryLevel(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Solar Battery Level sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_solar_battery_level"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Solar Battery"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Battery Level"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "batteryLevel" in component_status:
                battery = (
                    component_status["batteryLevel"].get("battery", {}).get("value")
                )
                if battery is not None:
                    try:
                        return float(battery)
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
        battery = self.native_value
        if battery is not None:
            if battery <= 10:
                return "mdi:battery-10"
            elif battery <= 20:
                return "mdi:battery-20"
            elif battery <= 30:
                return "mdi:battery-30"
            elif battery <= 40:
                return "mdi:battery-40"
            elif battery <= 50:
                return "mdi:battery-50"
            elif battery <= 60:
                return "mdi:battery-60"
            elif battery <= 70:
                return "mdi:battery-70"
            elif battery <= 80:
                return "mdi:battery-80"
            elif battery <= 90:
                return "mdi:battery-90"
            else:
                return "mdi:battery"
        return "mdi:battery-unknown"


class SmartThingsSolarEnergyProduction(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Solar Energy Production sensor."""

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
        self._attr_unique_id = f"{DOMAIN}_{device_id}_solar_energy_production"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Solar System"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Total Energy Production"

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
                        # Convert Wh to kWh
                        return float(energy) / 1000.0
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
        return "mdi:solar-panel"
