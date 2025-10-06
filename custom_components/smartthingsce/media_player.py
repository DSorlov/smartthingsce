"""Media Player platform for SmartThings Community Edition."""
from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
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
    """Set up the SmartThings media player platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []
    for device_id, device in coordinator.devices.items():
        capability_ids = get_device_capabilities(device)
        
        # Check for media player capabilities
        if any(cap in capability_ids for cap in ["mediaPlayback", "audioVolume", "tvChannel", "mediaInputSource"]):
            _LOGGER.info("Creating media player for device %s", device.get("label", device_id))
            entities.append(SmartThingsMediaPlayer(coordinator, api, device_id))

    async_add_entities(entities)


class SmartThingsMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Representation of a SmartThings media player."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, api, device_id: str) -> None:
        """Initialize the media player."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_media_player"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.devices.get(self._device_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("label", device.get("name", "Unknown")),
            manufacturer=device.get("manufacturerName", "SmartThings"),
            model=device.get("deviceTypeName", "Media Player"),
            sw_version=DEVICE_VERSION,
        )

    @property
    def name(self) -> str:
        """Return the name of the media player."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("label", device.get("name", "Media Player"))

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        device = self.coordinator.devices.get(self._device_id, {})
        capability_ids = get_device_capabilities(device)
        
        features = MediaPlayerEntityFeature(0)
        
        if "mediaPlayback" in capability_ids:
            features |= (
                MediaPlayerEntityFeature.PLAY |
                MediaPlayerEntityFeature.PAUSE |
                MediaPlayerEntityFeature.STOP |
                MediaPlayerEntityFeature.PREVIOUS_TRACK |
                MediaPlayerEntityFeature.NEXT_TRACK
            )
            
        if "audioVolume" in capability_ids:
            features |= (
                MediaPlayerEntityFeature.VOLUME_SET |
                MediaPlayerEntityFeature.VOLUME_MUTE |
                MediaPlayerEntityFeature.VOLUME_STEP
            )
            
        if "switch" in capability_ids:
            features |= MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF
            
        if "mediaInputSource" in capability_ids:
            features |= MediaPlayerEntityFeature.SELECT_SOURCE
            
        return features

    @property
    def state(self) -> MediaPlayerState:
        """State of the player."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})
        
        # Check switch state first
        for component_id, component_status in status.items():
            if "switch" in component_status:
                switch_state = component_status["switch"].get("switch", {}).get("value")
                if switch_state == "off":
                    return MediaPlayerState.OFF
        
        # Check media playback state
        for component_id, component_status in status.items():
            if "mediaPlayback" in component_status:
                playback_status = component_status["mediaPlayback"].get("playbackStatus", {}).get("value")
                if playback_status == "playing":
                    return MediaPlayerState.PLAYING
                elif playback_status == "paused":
                    return MediaPlayerState.PAUSED
                elif playback_status == "stopped":
                    return MediaPlayerState.IDLE
        
        return MediaPlayerState.ON

    @property
    def volume_level(self) -> Optional[float]:
        """Volume level of the media player (0..1)."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})
        
        for component_id, component_status in status.items():
            if "audioVolume" in component_status:
                volume = component_status["audioVolume"].get("volume", {}).get("value")
                if volume is not None:
                    try:
                        return float(volume) / 100.0
                    except (ValueError, TypeError):
                        pass
        return None

    @property
    def is_volume_muted(self) -> Optional[bool]:
        """Boolean if volume is currently muted."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})
        
        for component_id, component_status in status.items():
            if "audioMute" in component_status:
                mute_state = component_status["audioMute"].get("mute", {}).get("value")
                return mute_state == "muted"
            elif "audioVolume" in component_status:
                # Some devices use volume 0 as mute
                volume = component_status["audioVolume"].get("volume", {}).get("value")
                if volume is not None and volume == 0:
                    return True
        return None

    @property
    def source(self) -> Optional[str]:
        """Name of the current input source."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})
        
        for component_id, component_status in status.items():
            if "mediaInputSource" in component_status:
                input_source = component_status["mediaInputSource"].get("inputSource", {}).get("value")
                return input_source
            elif "tvChannel" in component_status:
                channel = component_status["tvChannel"].get("tvChannel", {}).get("value")
                return f"Channel {channel}" if channel else None
        return None

    @property
    def source_list(self) -> Optional[list[str]]:
        """List of available input sources."""
        device = self.coordinator.devices.get(self._device_id, {})
        status = device.get("status", {})
        
        for component_id, component_status in status.items():
            if "mediaInputSource" in component_status:
                supported_sources = component_status["mediaInputSource"].get("supportedInputSources", {}).get("value", [])
                return supported_sources
        return None

    @property
    def media_content_type(self) -> Optional[str]:
        """Content type of current playing media."""
        return MediaType.CHANNEL

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.devices.get(self._device_id, {})
        return device.get("status") is not None

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "switch",
                "on",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on media player %s: %s", self._device_id, err)

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "switch",
                "off",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off media player %s: %s", self._device_id, err)

    async def async_media_play(self) -> None:
        """Send play command."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "mediaPlayback",
                "play",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to play media %s: %s", self._device_id, err)

    async def async_media_pause(self) -> None:
        """Send pause command."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "mediaPlayback",
                "pause",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to pause media %s: %s", self._device_id, err)

    async def async_media_stop(self) -> None:
        """Send stop command."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "mediaPlayback",
                "stop",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to stop media %s: %s", self._device_id, err)

    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "mediaPlayback",
                "rewind",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to go to previous track %s: %s", self._device_id, err)

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "mediaPlayback",
                "fastForward",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to go to next track %s: %s", self._device_id, err)

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        try:
            volume_percent = int(volume * 100)
            await self._api.send_device_command(
                self._device_id,
                "audioVolume",
                "setVolume",
                [volume_percent],
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set volume %s: %s", self._device_id, err)

    async def async_volume_up(self) -> None:
        """Volume up the media player."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "audioVolume",
                "volumeUp",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to volume up %s: %s", self._device_id, err)

    async def async_volume_down(self) -> None:
        """Volume down the media player."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "audioVolume",
                "volumeDown",
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to volume down %s: %s", self._device_id, err)

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        try:
            command = "mute" if mute else "unmute"
            await self._api.send_device_command(
                self._device_id,
                "audioMute",
                command,
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to mute/unmute %s: %s", self._device_id, err)

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        try:
            await self._api.send_device_command(
                self._device_id,
                "mediaInputSource",
                "setInputSource",
                [source],
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to select source %s: %s", self._device_id, err)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:television"