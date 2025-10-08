"""Pool/Spa Controller platform for SmartThings Community Edition."""

from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import (
    UnitOfTemperature,
    ATTR_TEMPERATURE,
    PERCENTAGE,
    CONCENTRATION_PARTS_PER_MILLION,
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
    """Set up the SmartThings pool/spa controller platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []
    for device_id, device in coordinator.devices.items():
        capability_ids = get_device_capabilities(device)

        # Pool/Spa devices - check for pool-specific capabilities
        is_pool_device = any(
            cap in capability_ids
            for cap in [
                "poolController",
                "poolHeater",
                "poolPump",
                "poolChlorine",
                "poolPH",
            ]
        )

        # Also check device type/name for pool equipment
        device_type = device.get("deviceTypeName", "").lower()
        device_label = device.get("label", "").lower()
        if any(
            keyword in device_type or keyword in device_label
            for keyword in ["pool", "spa", "hot tub", "chlorine", "heater"]
        ):
            is_pool_device = True

        if is_pool_device:
            device_label = device.get("label", device_id)

            # Pool Controller (main status)
            if "poolController" in capability_ids:
                _LOGGER.info(
                    "Creating pool controller status sensor for device %s", device_label
                )
                entities.append(
                    SmartThingsPoolControllerStatus(coordinator, api, device_id)
                )

            # Pool Heater (temperature control)
            if "poolHeater" in capability_ids or (
                "temperatureMeasurement" in capability_ids
                and "thermostatHeatingSetpoint" in capability_ids
            ):
                _LOGGER.info(
                    "Creating pool heater thermostat for device %s", device_label
                )
                entities.append(
                    SmartThingsPoolHeaterThermostat(coordinator, api, device_id)
                )

            # Pool Pump control
            if "poolPump" in capability_ids:
                _LOGGER.info("Creating pool pump control for device %s", device_label)
                entities.append(SmartThingsPoolPumpControl(coordinator, api, device_id))
                entities.append(SmartThingsPoolPumpSpeed(coordinator, api, device_id))

            # Pool Temperature sensor (separate from heater control)
            if "temperatureMeasurement" in capability_ids:
                _LOGGER.info(
                    "Creating pool temperature sensor for device %s", device_label
                )
                entities.append(SmartThingsPoolTemperature(coordinator, api, device_id))

            # Pool Chlorine Level
            if "poolChlorine" in capability_ids:
                _LOGGER.info(
                    "Creating pool chlorine sensor for device %s", device_label
                )
                entities.append(SmartThingsPoolChlorine(coordinator, api, device_id))

            # Pool pH Level
            if "poolPH" in capability_ids:
                _LOGGER.info("Creating pool pH sensor for device %s", device_label)
                entities.append(SmartThingsPoolPH(coordinator, api, device_id))

    async_add_entities(entities)


class SmartThingsPoolControllerStatus(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Pool Controller Status sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_pool_controller_status"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Pool Controller"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Controller Status"

    @property
    def native_value(self) -> Optional[str]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "poolController" in component_status:
                controller_status = (
                    component_status["poolController"]
                    .get("poolStatus", {})
                    .get("value")
                )
                return controller_status

        return None

    @property
    def options(self) -> list[str]:
        """Return the list of available options."""
        return ["normal", "service", "timeout", "priming", "freeze", "error"]

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
            if "normal" in status_lower:
                return "mdi:pool"
            elif "service" in status_lower:
                return "mdi:tools"
            elif "error" in status_lower or "timeout" in status_lower:
                return "mdi:alert-circle"
            elif "freeze" in status_lower:
                return "mdi:snowflake"
            elif "priming" in status_lower:
                return "mdi:pump"
        return "mdi:swimming"


class SmartThingsPoolHeaterThermostat(CoordinatorEntity, ClimateEntity):
    """Representation of a SmartThings Pool Heater thermostat."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the thermostat."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_pool_heater"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Pool Heater"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the thermostat."""
        return "Pool Heater"

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation mode."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "poolHeater" in component_status:
                heater_status = (
                    component_status["poolHeater"].get("heaterStatus", {}).get("value")
                )
                if heater_status == "heating":
                    return HVACMode.HEAT
                elif heater_status == "off":
                    return HVACMode.OFF
            elif "switch" in component_status:
                switch_state = component_status["switch"].get("switch", {}).get("value")
                if switch_state == "on":
                    return HVACMode.HEAT
                else:
                    return HVACMode.OFF

        return HVACMode.OFF

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
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
    def target_temperature(self) -> Optional[float]:
        """Return the target temperature."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "thermostatHeatingSetpoint" in component_status:
                setpoint = (
                    component_status["thermostatHeatingSetpoint"]
                    .get("heatingSetpoint", {})
                    .get("value")
                )
                if setpoint is not None:
                    try:
                        return float(setpoint)
                    except (ValueError, TypeError):
                        pass
            elif "poolHeater" in component_status:
                setpoint = (
                    component_status["poolHeater"]
                    .get("targetTemperature", {})
                    .get("value")
                )
                if setpoint is not None:
                    try:
                        return float(setpoint)
                    except (ValueError, TypeError):
                        pass

        return None

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return 10.0  # 50°F

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return 45.0  # 113°F

    @property
    def target_temperature_step(self) -> float:
        """Return the supported step of target temperature."""
        return 0.5

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        try:
            if hvac_mode == HVACMode.HEAT:
                await self._api.send_device_command(
                    self._device_id,
                    "switch",
                    "on",
                )
            elif hvac_mode == HVACMode.OFF:
                await self._api.send_device_command(
                    self._device_id,
                    "switch",
                    "off",
                )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to set HVAC mode for pool heater %s: %s", self._device_id, err
            )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        try:
            await self._api.send_device_command(
                self._device_id,
                "thermostatHeatingSetpoint",
                "setHeatingSetpoint",
                [int(temperature)],
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to set temperature for pool heater %s: %s", self._device_id, err
            )

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:water-thermometer"


class SmartThingsPoolPumpControl(CoordinatorEntity, SwitchEntity):
    """Representation of a SmartThings Pool Pump Control switch."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_pool_pump_control"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Pool Pump"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return "Pool Pump"

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if pump is on."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "poolPump" in component_status:
                pump_status = (
                    component_status["poolPump"].get("pumpStatus", {}).get("value")
                )
                return pump_status == "on"
            elif "switch" in component_status:
                switch_state = component_status["switch"].get("switch", {}).get("value")
                return switch_state == "on"

        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the pump on."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "poolPump",
                "on",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on pool pump %s: %s", self._device_id, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the pump off."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "poolPump",
                "off",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off pool pump %s: %s", self._device_id, err)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:pump"


class SmartThingsPoolPumpSpeed(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Pool Pump Speed sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_pool_pump_speed"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Pool Pump"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Pump Speed"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "poolPump" in component_status:
                speed = component_status["poolPump"].get("pumpSpeed", {}).get("value")
                if speed is not None:
                    try:
                        return float(speed)
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


class SmartThingsPoolTemperature(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Pool Temperature sensor."""

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
        self._attr_unique_id = f"{DOMAIN}_{device_id}_pool_temperature"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Pool Sensor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Pool Temperature"

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
        return "mdi:thermometer-water"


class SmartThingsPoolChlorine(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Pool Chlorine sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_pool_chlorine"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Pool Chemical Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Chlorine Level"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "poolChlorine" in component_status:
                chlorine = (
                    component_status["poolChlorine"]
                    .get("chlorineLevel", {})
                    .get("value")
                )
                if chlorine is not None:
                    try:
                        return float(chlorine)
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
        chlorine = self.native_value
        if chlorine is not None:
            if chlorine < 1.0:
                return "mdi:water-alert"
            elif chlorine > 3.0:
                return "mdi:water-off"
            else:
                return "mdi:water-check"
        return "mdi:water"


class SmartThingsPoolPH(CoordinatorEntity, SensorEntity):
    """Representation of a SmartThings Pool pH sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_pool_ph"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Pool Chemical Monitor"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "pH Level"

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "poolPH" in component_status:
                ph = component_status["poolPH"].get("phLevel", {}).get("value")
                if ph is not None:
                    try:
                        return float(ph)
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
        ph = self.native_value
        if ph is not None:
            if ph < 7.2:
                return "mdi:ph-minus"
            elif ph > 7.6:
                return "mdi:ph-plus"
            else:
                return "mdi:ph"
        return "mdi:test-tube"
