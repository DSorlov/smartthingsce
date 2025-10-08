"""Camera platform for SmartThings Community Edition."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any, Optional

from homeassistant.components.camera import (
    Camera,
    CameraEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
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
    """Set up the SmartThings camera platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []
    for device_id, device in coordinator.devices.items():
        capability_ids = get_device_capabilities(device)

        # Check for camera capabilities
        if any(
            cap in capability_ids
            for cap in ["videoStream", "imageCapture", "videoCapture"]
        ):
            _LOGGER.info(
                "Creating camera for device %s", device.get("label", device_id)
            )
            entities.append(SmartThingsCamera(coordinator, api, device_id))

    async_add_entities(entities)


class SmartThingsCamera(CoordinatorEntity, Camera):
    """Representation of a SmartThings Camera."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the camera."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_camera"
        self._session = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Camera"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the camera."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("label", device.get("name", "Camera"))

    @property
    def supported_features(self) -> CameraEntityFeature:
        """Return supported features."""
        device = self.coordinator.devices.get(self._device_id, {})
        capability_ids = get_device_capabilities(device)

        features = CameraEntityFeature(0)

        if "videoStream" in capability_ids:
            features |= CameraEntityFeature.STREAM

        return features

    @property
    def is_on(self) -> bool:
        """Return true if camera is on."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        # Check switch capability for power state
        for component_id, component_status in status.items():
            if "switch" in component_status:
                switch_state = component_status["switch"].get("switch", {}).get("value")
                return switch_state == "on"

        # If no switch capability, assume camera is always on
        return True

    @property
    def is_streaming(self) -> bool:
        """Return true if camera is streaming."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "videoStream" in component_status:
                stream_status = (
                    component_status["videoStream"].get("stream", {}).get("value")
                )
                return stream_status == "active"

        return False

    @property
    def motion_detection_enabled(self) -> bool:
        """Return the camera motion detection status."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "motionSensor" in component_status:
                # If motion sensor capability exists, it's enabled
                return True

        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})
        attributes = {}

        # Add camera-specific attributes
        for component_id, component_status in status.items():
            # Video stream attributes
            if "videoStream" in component_status:
                video_data = component_status["videoStream"]
                for key, value_dict in video_data.items():
                    if isinstance(value_dict, dict) and "value" in value_dict:
                        attributes[f"video_{key}"] = value_dict["value"]

            # Image capture attributes
            if "imageCapture" in component_status:
                image_data = component_status["imageCapture"]
                for key, value_dict in image_data.items():
                    if isinstance(value_dict, dict) and "value" in value_dict:
                        attributes[f"image_{key}"] = value_dict["value"]

            # Motion detection
            if "motionSensor" in component_status:
                motion = component_status["motionSensor"].get("motion", {}).get("value")
                attributes["motion_detected"] = motion == "active"

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_camera_image(
        self, width: Optional[int] = None, height: Optional[int] = None
    ) -> Optional[bytes]:
        """Return a still image response from the camera."""
        try:
            # Try to get image from imageCapture capability
            device = self.coordinator.devices.get(self._device_id, {})
            status = device.get("status", {})

            image_url = None
            for component_id, component_status in status.items():
                if "imageCapture" in component_status:
                    # Look for image URL or base64 data
                    image_data = component_status["imageCapture"]

                    if "image" in image_data:
                        image_info = image_data["image"].get("value")
                        if isinstance(image_info, dict):
                            image_url = image_info.get("url")
                        elif isinstance(image_info, str):
                            # Might be a direct URL
                            image_url = image_info

                    # Alternative: encrypted image URL
                    if not image_url and "encryptedImage" in image_data:
                        encrypted_info = image_data["encryptedImage"].get("value", {})
                        if isinstance(encrypted_info, dict):
                            image_url = encrypted_info.get("url")

                    break

            if image_url:
                if not self._session:
                    self._session = async_get_clientsession(self.hass)

                # Fetch the image
                async with asyncio.timeout(10):
                    async with self._session.get(image_url) as response:
                        if response.status == 200:
                            return await response.read()
                        else:
                            _LOGGER.warning(
                                "Failed to fetch camera image: HTTP %d", response.status
                            )

            # Fallback: try to capture a new image
            await self._api.send_device_command(
                self._device_id,
                "imageCapture",
                "take",
            )

            # Wait a moment and try again
            await asyncio.sleep(2)
            await self.coordinator.async_request_refresh()

            # Try to get the updated image URL
            device = self.coordinator.devices.get(self._device_id, {})
            status = device.get("status", {})

            for component_id, component_status in status.items():
                if "imageCapture" in component_status:
                    image_data = component_status["imageCapture"]
                    if "image" in image_data:
                        image_info = image_data["image"].get("value")
                        if isinstance(image_info, dict):
                            image_url = image_info.get("url")
                        elif isinstance(image_info, str):
                            image_url = image_info

                        if image_url and self._session:
                            async with asyncio.timeout(10):
                                async with self._session.get(image_url) as response:
                                    if response.status == 200:
                                        return await response.read()
                    break

            _LOGGER.warning(
                "Unable to retrieve camera image for device %s", self._device_id
            )
            return None

        except Exception as err:
            _LOGGER.error(
                "Failed to retrieve camera image %s: %s", self._device_id, err
            )
            return None

    async def stream_source(self) -> Optional[str]:
        """Return the source of the stream."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})

        for component_id, component_status in status.items():
            if "videoStream" in component_status:
                stream_data = component_status["videoStream"]

                # Look for stream URL
                if "stream" in stream_data:
                    stream_info = stream_data["stream"].get("value")
                    if isinstance(stream_info, dict):
                        return stream_info.get("url")
                    elif isinstance(stream_info, str) and stream_info.startswith(
                        "http"
                    ):
                        return stream_info

                # Alternative: URI field
                if "uri" in stream_data:
                    uri = stream_data["uri"].get("value")
                    if uri:
                        return uri

        return None

    async def async_turn_on(self) -> None:
        """Turn on camera."""
        try:
            # Try to turn on via switch capability
            await self._api.send_device_command(
                self._device_id,
                "switch",
                "on",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on camera %s: %s", self._device_id, err)

    async def async_turn_off(self) -> None:
        """Turn off camera."""
        try:
            # Try to turn off via switch capability
            await self._api.send_device_command(
                self._device_id,
                "switch",
                "off",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off camera %s: %s", self._device_id, err)

    async def async_enable_motion_detection(self) -> None:
        """Enable motion detection in the camera."""
        try:
            # Some cameras support motion detection enable/disable
            await self._api.send_device_command(
                self._device_id,
                "motionSensor",
                "enable",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.debug(
                "Motion detection control not supported for camera %s: %s",
                self._device_id,
                err,
            )

    async def async_disable_motion_detection(self) -> None:
        """Disable motion detection in the camera."""
        try:
            # Some cameras support motion detection enable/disable
            await self._api.send_device_command(
                self._device_id,
                "motionSensor",
                "disable",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.debug(
                "Motion detection control not supported for camera %s: %s",
                self._device_id,
                err,
            )

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:camera"
