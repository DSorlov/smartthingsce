"""Light platform for SmartThings Community Edition."""

import logging
from typing import Any, Optional

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.color import (
    color_hs_to_RGB,
    color_RGB_to_hs,
    color_temperature_kelvin_to_mired,
    color_temperature_mired_to_kelvin,
)

from .const import ATTRIBUTION, DOMAIN, DEVICE_VERSION, get_device_capabilities

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SmartThings lights."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []

    for device_id, device in coordinator.devices.items():
        # Get capabilities from the main component
        capability_ids = get_device_capabilities(device)

        # Check if device has any light capability
        has_light = any(
            cap_id in ["switchLevel", "colorControl", "colorTemperature"]
            for cap_id in capability_ids
        )

        if has_light:
            entities.append(SmartThingsLight(coordinator, api, device_id))

    async_add_entities(entities)


class SmartThingsLight(CoordinatorEntity, LightEntity):
    """Representation of a SmartThings light."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the light."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_light"

        # Determine supported color modes
        capabilities = self._get_capabilities()
        self._attr_supported_color_modes = set()

        if "colorControl" in capabilities:
            self._attr_supported_color_modes.add(ColorMode.HS)
        elif "colorTemperature" in capabilities:
            self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)
        elif "switchLevel" in capabilities:
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
        else:
            self._attr_supported_color_modes.add(ColorMode.ONOFF)

    def _get_capabilities(self) -> list:
        """Get device capabilities."""
        device = self.coordinator.devices.get(self._device_id, {})
        capabilities = (
            device.get("components", {}).get("main", {}).get("capabilities", [])
        )
        return [cap.get("id") for cap in capabilities]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Light"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the light."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("label", device.get("name", "Light"))

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if light is on."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {}).get("main", {}).get("switch", {})
        switch_state = status.get("switch", {}).get("value")
        return switch_state == "on"

    @property
    def brightness(self) -> Optional[int]:
        """Return the brightness of the light."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {}).get("main", {}).get("switchLevel", {})
        level = status.get("level", {}).get("value")

        if level is not None:
            return int(level * 255 / 100)

        return None

    @property
    def hs_color(self) -> Optional[tuple]:
        """Return the hue and saturation color value."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {}).get("main", {}).get("colorControl", {})
        hue = status.get("hue", {}).get("value")
        saturation = status.get("saturation", {}).get("value")

        if hue is not None and saturation is not None:
            return (hue * 360 / 100, saturation)

        return None

    @property
    def color_temp(self) -> Optional[int]:
        """Return the color temperature."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {}).get("main", {}).get("colorTemperature", {})
        kelvin = status.get("colorTemperature", {}).get("value")

        if kelvin is not None:
            return color_temperature_kelvin_to_mired(kelvin)

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        try:
            # Turn on the switch
            await self._api.send_device_command(
                self._device_id,
                "switch",
                "on",
            )

            # Set brightness if provided
            if ATTR_BRIGHTNESS in kwargs:
                brightness = int(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
                await self._api.send_device_command(
                    self._device_id,
                    "switchLevel",
                    "setLevel",
                    [brightness],
                )

            # Set color if provided
            if ATTR_HS_COLOR in kwargs:
                hue, saturation = kwargs[ATTR_HS_COLOR]
                hue_100 = int(hue * 100 / 360)
                await self._api.send_device_command(
                    self._device_id,
                    "colorControl",
                    "setColor",
                    [{"hue": hue_100, "saturation": int(saturation)}],
                )

            # Set color temperature if provided
            if ATTR_COLOR_TEMP_KELVIN in kwargs:
                kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]
                await self._api.send_device_command(
                    self._device_id,
                    "colorTemperature",
                    "setColorTemperature",
                    [int(kelvin)],
                )

            await self.coordinator.async_request_refresh()

        except Exception as err:
            _LOGGER.error("Failed to turn on light %s: %s", self._device_id, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "switch",
                "off",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off light %s: %s", self._device_id, err)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:lightbulb"
