"""Traditional thermostat platform for SmartThings Community Edition."""

from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_ON,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DEVICE_VERSION, DOMAIN, get_device_capabilities

_LOGGER = logging.getLogger(__name__)

# SmartThings to HA HVAC mode mapping
SMARTTHINGS_HVAC_MODES = {
    "auto": HVACMode.AUTO,
    "cool": HVACMode.COOL,
    "heat": HVACMode.HEAT,
    "emergencyHeat": HVACMode.HEAT,
    "off": HVACMode.OFF,
    "fanOnly": HVACMode.FAN_ONLY,
    "dryair": HVACMode.DRY,
}

# SmartThings to HA HVAC action mapping
SMARTTHINGS_HVAC_ACTIONS = {
    "heating": HVACAction.HEATING,
    "cooling": HVACAction.COOLING,
    "fan only": HVACAction.FAN,
    "idle": HVACAction.IDLE,
    "off": HVACAction.OFF,
}

# SmartThings fan modes
SMARTTHINGS_FAN_MODES = {
    "auto": FAN_AUTO,
    "on": FAN_ON,
    "circulate": "circulate",
    "followschedule": "followschedule",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SmartThings traditional thermostat devices."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []

    for device_id, device in coordinator.devices.items():
        capability_ids = get_device_capabilities(device)

        # Create thermostat entity for devices with thermostatMode capability
        # This is different from refrigerator thermostats which only have thermostatCoolingSetpoint
        if "thermostatMode" in capability_ids:
            _LOGGER.info(
                "Creating traditional thermostat for device %s",
                device.get("label", device_id),
            )
            entities.append(
                SmartThingsTraditionalThermostat(coordinator, api, device_id)
            )

    async_add_entities(entities)


class SmartThingsTraditionalThermostat(CoordinatorEntity, ClimateEntity):
    """Representation of a SmartThings traditional thermostat (HVAC system)."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator,
        api,
        device_id: str,
    ):
        """Initialize the thermostat."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_traditional_thermostat"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Thermostat"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the thermostat."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("label", device.get("name", "Thermostat"))

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        device = self.coordinator.devices.get(self._device_id, {})
        capability_ids = get_device_capabilities(device)

        features = ClimateEntityFeature(0)

        if "thermostatHeatingSetpoint" in capability_ids:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE

        if "thermostatCoolingSetpoint" in capability_ids:
            if features & ClimateEntityFeature.TARGET_TEMPERATURE:
                # Has both heating and cooling - use target temperature range
                features |= ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
            else:
                features |= ClimateEntityFeature.TARGET_TEMPERATURE

        if "thermostatFanMode" in capability_ids:
            features |= ClimateEntityFeature.FAN_MODE

        return features

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available hvac operation modes."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        # Get supported modes from device status
        for component_id, component_status in status.items():
            if "thermostatMode" in component_status:
                supported_modes = (
                    component_status["thermostatMode"]
                    .get("supportedThermostatModes", {})
                    .get("value", [])
                )
                if supported_modes:
                    return [
                        SMARTTHINGS_HVAC_MODES.get(mode, HVACMode.OFF)
                        for mode in supported_modes
                    ]

        # Default modes
        return [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO]

    @property
    def hvac_mode(self) -> Optional[HVACMode]:
        """Return current operation mode."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "thermostatMode" in component_status:
                mode = (
                    component_status["thermostatMode"]
                    .get("thermostatMode", {})
                    .get("value")
                )
                return SMARTTHINGS_HVAC_MODES.get(mode, HVACMode.OFF)

        return HVACMode.OFF

    @property
    def hvac_action(self) -> Optional[HVACAction]:
        """Return the current running hvac operation."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "thermostatOperatingState" in component_status:
                operating_state = (
                    component_status["thermostatOperatingState"]
                    .get("thermostatOperatingState", {})
                    .get("value")
                )
                return SMARTTHINGS_HVAC_ACTIONS.get(operating_state, HVACAction.IDLE)

        return HVACAction.IDLE

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "temperatureMeasurement" in component_status:
                temp_data = component_status["temperatureMeasurement"].get(
                    "temperature", {}
                )
                temp_value = temp_data.get("value")
                if temp_value is not None:
                    try:
                        return float(temp_value)
                    except (ValueError, TypeError):
                        pass

        return None

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the temperature we try to reach."""
        # For single setpoint mode, return the active setpoint
        current_mode = self.hvac_mode

        if current_mode == HVACMode.HEAT:
            return self.target_temperature_low
        elif current_mode == HVACMode.COOL:
            return self.target_temperature_high
        elif current_mode == HVACMode.AUTO:
            # In auto mode, return the average of high and low
            low = self.target_temperature_low
            high = self.target_temperature_high
            if low is not None and high is not None:
                return (low + high) / 2

        return None

    @property
    def target_temperature_high(self) -> Optional[float]:
        """Return the highbound target temperature we try to reach."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "thermostatCoolingSetpoint" in component_status:
                setpoint_data = component_status["thermostatCoolingSetpoint"].get(
                    "coolingSetpoint", {}
                )
                setpoint_value = setpoint_data.get("value")
                if setpoint_value is not None:
                    try:
                        return float(setpoint_value)
                    except (ValueError, TypeError):
                        pass

        return None

    @property
    def target_temperature_low(self) -> Optional[float]:
        """Return the lowbound target temperature we try to reach."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "thermostatHeatingSetpoint" in component_status:
                setpoint_data = component_status["thermostatHeatingSetpoint"].get(
                    "heatingSetpoint", {}
                )
                setpoint_value = setpoint_data.get("value")
                if setpoint_value is not None:
                    try:
                        return float(setpoint_value)
                    except (ValueError, TypeError):
                        pass

        return None

    @property
    def fan_mode(self) -> Optional[str]:
        """Return the fan setting."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "thermostatFanMode" in component_status:
                fan_mode = (
                    component_status["thermostatFanMode"]
                    .get("thermostatFanMode", {})
                    .get("value")
                )
                return SMARTTHINGS_FAN_MODES.get(fan_mode, fan_mode)

        return None

    @property
    def fan_modes(self) -> Optional[list[str]]:
        """Return the list of available fan modes."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "thermostatFanMode" in component_status:
                supported_modes = (
                    component_status["thermostatFanMode"]
                    .get("supportedThermostatFanModes", {})
                    .get("value", [])
                )
                if supported_modes:
                    return [
                        SMARTTHINGS_FAN_MODES.get(mode, mode)
                        for mode in supported_modes
                    ]

        return None

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return 7.0  # 45°F

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return 35.0  # 95°F

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
        # Convert HA mode back to SmartThings mode
        st_mode = None
        for st_key, ha_value in SMARTTHINGS_HVAC_MODES.items():
            if ha_value == hvac_mode:
                st_mode = st_key
                break

        if st_mode is None:
            _LOGGER.error("Unsupported HVAC mode: %s", hvac_mode)
            return

        try:
            await self._api.send_device_command(
                self._device_id,
                "thermostatMode",
                "setThermostatMode",
                [st_mode],
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to set HVAC mode for device %s: %s", self._device_id, err
            )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        target_temp_low = kwargs.get("target_temp_low")
        target_temp_high = kwargs.get("target_temp_high")
        temperature = kwargs.get(ATTR_TEMPERATURE)

        try:
            # Handle temperature range (dual setpoint)
            if target_temp_low is not None:
                await self._api.send_device_command(
                    self._device_id,
                    "thermostatHeatingSetpoint",
                    "setHeatingSetpoint",
                    [int(target_temp_low)],
                )

            if target_temp_high is not None:
                await self._api.send_device_command(
                    self._device_id,
                    "thermostatCoolingSetpoint",
                    "setCoolingSetpoint",
                    [int(target_temp_high)],
                )

            # Handle single temperature (based on current mode)
            if (
                temperature is not None
                and target_temp_low is None
                and target_temp_high is None
            ):
                current_mode = self.hvac_mode

                if current_mode == HVACMode.HEAT:
                    await self._api.send_device_command(
                        self._device_id,
                        "thermostatHeatingSetpoint",
                        "setHeatingSetpoint",
                        [int(temperature)],
                    )
                elif current_mode == HVACMode.COOL:
                    await self._api.send_device_command(
                        self._device_id,
                        "thermostatCoolingSetpoint",
                        "setCoolingSetpoint",
                        [int(temperature)],
                    )
                else:
                    _LOGGER.warning(
                        "Cannot set single temperature in mode %s", current_mode
                    )

            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to set temperature for device %s: %s", self._device_id, err
            )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        # Convert HA fan mode back to SmartThings fan mode
        st_fan_mode = None
        for st_key, ha_value in SMARTTHINGS_FAN_MODES.items():
            if ha_value == fan_mode:
                st_fan_mode = st_key
                break

        # If not found in mapping, use the value directly
        if st_fan_mode is None:
            st_fan_mode = fan_mode

        try:
            await self._api.send_device_command(
                self._device_id,
                "thermostatFanMode",
                "setThermostatFanMode",
                [st_fan_mode],
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to set fan mode for device %s: %s", self._device_id, err
            )

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:thermostat"
