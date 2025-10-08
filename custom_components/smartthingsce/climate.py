"""Climate platform for SmartThings Community Edition."""

import logging
from typing import Any, Optional

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
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


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SmartThings climate devices."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []

    for device_id, device in coordinator.devices.items():
        # Get capabilities from the main component
        capability_ids = get_device_capabilities(device)

        # Create climate entity for thermostatCoolingSetpoint capability
        if "thermostatCoolingSetpoint" in capability_ids:
            entities.append(
                SmartThingsThermostat(
                    coordinator,
                    api,
                    device_id,
                )
            )

    async_add_entities(entities)


class SmartThingsThermostat(CoordinatorEntity, ClimateEntity):
    """Representation of a SmartThings thermostat (refrigerator temperature control)."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.COOL]  # Refrigerators only cool
    _attr_hvac_mode = HVACMode.COOL

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
        self._attr_unique_id = f"{device_id}_thermostat"
        self._attr_name = "Temperature Control"

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
            "model": device.get("deviceTypeName", "Climate"),
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
                if (
                    ver.get("description") == "Micom"
                    and ver.get("swType") == "Firmware"
                ):
                    device_info["sw_version"] = ver.get("versionNumber")
                    break

        software_update = main_status.get("samsungce.softwareUpdate", {})
        if software_update:
            otn_duid = software_update.get("otnDUID", {}).get("value")
            if otn_duid:
                device_info["model"] = otn_duid

        return DeviceInfo(**device_info)

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        device = self.coordinator.devices.get(self._device_id, {})
        device_status = device.get("status", {})

        # Try to find temperature in any component
        for component_id, component_data in device_status.items():
            if "temperatureMeasurement" in component_data:
                temp_data = component_data.get("temperatureMeasurement", {})
                temp_value = temp_data.get("temperature", {}).get("value")
                if temp_value is not None:
                    try:
                        return float(temp_value)
                    except (ValueError, TypeError):
                        pass

        return None

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the target temperature."""
        device = self.coordinator.devices.get(self._device_id, {})
        device_status = device.get("status", {})

        # Try to find cooling setpoint in any component
        for component_id, component_data in device_status.items():
            if "thermostatCoolingSetpoint" in component_data:
                setpoint_data = component_data.get("thermostatCoolingSetpoint", {})
                setpoint_value = setpoint_data.get("coolingSetpoint", {}).get("value")
                if setpoint_value is not None:
                    try:
                        return float(setpoint_value)
                    except (ValueError, TypeError):
                        pass

        return None

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        device = self.coordinator.devices.get(self._device_id, {})
        device_status = device.get("status", {})

        # Try to find cooling setpoint range in any component
        for component_id, component_data in device_status.items():
            if "thermostatCoolingSetpoint" in component_data:
                setpoint_data = component_data.get("thermostatCoolingSetpoint", {})
                range_value = setpoint_data.get("coolingSetpointRange", {}).get(
                    "value", {}
                )
                if isinstance(range_value, dict) and "minimum" in range_value:
                    try:
                        return float(range_value["minimum"])
                    except (ValueError, TypeError):
                        pass

        return -30.0  # Default minimum for refrigerators

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        device = self.coordinator.devices.get(self._device_id, {})
        device_status = device.get("status", {})

        # Try to find cooling setpoint range in any component
        for component_id, component_data in device_status.items():
            if "thermostatCoolingSetpoint" in component_data:
                setpoint_data = component_data.get("thermostatCoolingSetpoint", {})
                range_value = setpoint_data.get("coolingSetpointRange", {}).get(
                    "value", {}
                )
                if isinstance(range_value, dict) and "maximum" in range_value:
                    try:
                        return float(range_value["maximum"])
                    except (ValueError, TypeError):
                        pass

        return 10.0  # Default maximum for refrigerators

    @property
    def target_temperature_step(self) -> float:
        """Return the supported step of target temperature."""
        device = self.coordinator.devices.get(self._device_id, {})
        device_status = device.get("status", {})

        # Try to find cooling setpoint range in any component
        for component_id, component_data in device_status.items():
            if "thermostatCoolingSetpoint" in component_data:
                setpoint_data = component_data.get("thermostatCoolingSetpoint", {})
                range_value = setpoint_data.get("coolingSetpointRange", {}).get(
                    "value", {}
                )
                if isinstance(range_value, dict) and "step" in range_value:
                    try:
                        return float(range_value["step"])
                    except (ValueError, TypeError):
                        pass

        return 1.0  # Default step

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        device = self.coordinator.devices.get(self._device_id, {})
        device_status = device.get("status", {})

        # Find which component has thermostatCoolingSetpoint
        target_component = "main"
        for component_id, component_data in device_status.items():
            if "thermostatCoolingSetpoint" in component_data:
                target_component = component_id
                break

        try:
            # Send command to set cooling setpoint
            await self._api.send_device_command(
                self._device_id,
                "thermostatCoolingSetpoint",
                "setCoolingSetpoint",
                [int(temperature)],
                component=target_component,
            )
            # Request a coordinator refresh to update the state
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to set temperature for device %s: %s", self._device_id, err
            )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None
