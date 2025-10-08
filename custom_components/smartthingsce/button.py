"""Button platform for SmartThings Community Edition."""

from __future__ import annotations

import logging
from typing import Any, Optional
from datetime import datetime

from homeassistant.components.button import (
    ButtonEntity,
    ButtonDeviceClass,
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
    """Set up the SmartThings button platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []
    for device_id, device in coordinator.devices.items():
        capability_ids = get_device_capabilities(device)

        # Check for button capabilities
        if "button" in capability_ids:
            # Get number of buttons from device status
            device_status = device.get("status", {})
            button_count = 1  # Default to 1 button

            # Try to determine number of buttons
            for component_id, component_status in device_status.items():
                if "button" in component_status:
                    # Some devices report numberOfButtons
                    if "numberOfButtons" in component_status["button"]:
                        button_count = component_status["button"][
                            "numberOfButtons"
                        ].get("value", 1)
                    # Otherwise check supportedButtonValues
                    elif "supportedButtonValues" in component_status["button"]:
                        supported_values = component_status["button"][
                            "supportedButtonValues"
                        ].get("value", [])
                        if supported_values:
                            button_count = len(supported_values)
                    break

            # Create button entities for each button
            for button_number in range(1, button_count + 1):
                _LOGGER.info(
                    "Creating button %d for device %s",
                    button_number,
                    device.get("label", device_id),
                )
                entities.append(
                    SmartThingsButton(coordinator, api, device_id, button_number)
                )

        elif "holdableButton" in capability_ids:
            # Holdable buttons - typically scene controllers
            device_status = device.get("status", {})
            button_count = 1

            for component_id, component_status in device_status.items():
                if "holdableButton" in component_status:
                    if "numberOfButtons" in component_status["holdableButton"]:
                        button_count = component_status["holdableButton"][
                            "numberOfButtons"
                        ].get("value", 1)
                    elif "supportedButtonValues" in component_status["holdableButton"]:
                        supported_values = component_status["holdableButton"][
                            "supportedButtonValues"
                        ].get("value", [])
                        if supported_values:
                            button_count = len(supported_values)
                    break

            for button_number in range(1, button_count + 1):
                _LOGGER.info(
                    "Creating holdable button %d for device %s",
                    button_number,
                    device.get("label", device_id),
                )
                entities.append(
                    SmartThingsHoldableButton(
                        coordinator, api, device_id, button_number
                    )
                )

    async_add_entities(entities)


class SmartThingsButton(CoordinatorEntity, ButtonEntity):
    """Representation of a SmartThings button."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = ButtonDeviceClass.IDENTIFY

    def __init__(self, coordinator, api, device_id: str, button_number: int) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._button_number = button_number
        self._attr_unique_id = f"{DOMAIN}_{device_id}_button_{button_number}"
        self._last_pressed = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Button"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the button."""
        device = self.coordinator.devices.get(self._device_id, {})
        device_name = device.get("label", device.get("name", "Button"))

        # If only one button, use device name
        if self._get_button_count() == 1:
            return device_name

        return f"{device_name} Button {self._button_number}"

    def _get_button_count(self) -> int:
        """Get the total number of buttons on this device."""
        device = self.coordinator.devices.get(self._device_id, {})
        device_status = device.get("status", {})

        for component_id, component_status in device_status.items():
            if "button" in component_status:
                if "numberOfButtons" in component_status["button"]:
                    return component_status["button"]["numberOfButtons"].get("value", 1)
                elif "supportedButtonValues" in component_status["button"]:
                    supported_values = component_status["button"][
                        "supportedButtonValues"
                    ].get("value", [])
                    return len(supported_values) if supported_values else 1

        return 1

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        device = self.coordinator.devices.get(self._device_id, {})
        device_status = device.get("status", {})

        attributes = {}

        # Add button state information
        for component_id, component_status in device_status.items():
            if "button" in component_status:
                button_data = component_status["button"]

                # Add last button pressed info
                if "button" in button_data:
                    last_button_info = button_data["button"].get("value", {})
                    if isinstance(last_button_info, dict):
                        attributes["last_pressed_button"] = last_button_info.get(
                            "buttonNumber"
                        )
                        attributes["last_pressed_action"] = last_button_info.get(
                            "action"
                        )

                # Add supported button values
                if "supportedButtonValues" in button_data:
                    attributes["supported_actions"] = button_data[
                        "supportedButtonValues"
                    ].get("value", [])

                break

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_press(self) -> None:
        """Press the button."""
        try:
            # For SmartThings buttons, we can't actually trigger them remotely
            # This is more for status/event tracking, but we'll log the attempt
            _LOGGER.info(
                "Button press requested for button %d on device %s",
                self._button_number,
                self._device_id,
            )

            # Update last pressed time for state tracking
            self._last_pressed = datetime.now()

            # Some buttons might support a "push" command
            await self._api.send_device_command(
                self._device_id,
                "button",
                "push",
                [self._button_number],
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.debug(
                "Button %s may not support remote press: %s", self._device_id, err
            )

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:gesture-tap-button"


class SmartThingsHoldableButton(CoordinatorEntity, ButtonEntity):
    """Representation of a SmartThings holdable button (scene controller)."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = ButtonDeviceClass.IDENTIFY

    def __init__(self, coordinator, api, device_id: str, button_number: int) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._button_number = button_number
        self._attr_unique_id = f"{DOMAIN}_{device_id}_holdable_button_{button_number}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Scene Controller"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the button."""
        device = self.coordinator.devices.get(self._device_id, {})
        device_name = device.get("label", device.get("name", "Scene Controller"))

        # If only one button, use device name
        if self._get_button_count() == 1:
            return device_name

        return f"{device_name} Button {self._button_number}"

    def _get_button_count(self) -> int:
        """Get the total number of buttons on this device."""
        device = self.coordinator.devices.get(self._device_id, {})
        device_status = device.get("status", {})

        for component_id, component_status in device_status.items():
            if "holdableButton" in component_status:
                if "numberOfButtons" in component_status["holdableButton"]:
                    return component_status["holdableButton"]["numberOfButtons"].get(
                        "value", 1
                    )
                elif "supportedButtonValues" in component_status["holdableButton"]:
                    supported_values = component_status["holdableButton"][
                        "supportedButtonValues"
                    ].get("value", [])
                    return len(supported_values) if supported_values else 1

        return 1

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        device = self.coordinator.devices.get(self._device_id, {})
        device_status = device.get("status", {})

        attributes = {}

        # Add holdable button state information
        for component_id, component_status in device_status.items():
            if "holdableButton" in component_status:
                button_data = component_status["holdableButton"]

                # Add last button pressed info
                if "button" in button_data:
                    last_button_info = button_data["button"].get("value", {})
                    if isinstance(last_button_info, dict):
                        attributes["last_pressed_button"] = last_button_info.get(
                            "buttonNumber"
                        )
                        attributes["last_pressed_action"] = last_button_info.get(
                            "action"
                        )

                # Add supported button values
                if "supportedButtonValues" in button_data:
                    attributes["supported_actions"] = button_data[
                        "supportedButtonValues"
                    ].get("value", [])

                break

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_press(self) -> None:
        """Press the button."""
        try:
            _LOGGER.info(
                "Holdable button press requested for button %d on device %s",
                self._button_number,
                self._device_id,
            )

            # Try to send a push command for holdable buttons
            await self._api.send_device_command(
                self._device_id,
                "holdableButton",
                "push",
                [self._button_number],
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.debug(
                "Holdable button %s may not support remote press: %s",
                self._device_id,
                err,
            )

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:gesture-tap-hold"
