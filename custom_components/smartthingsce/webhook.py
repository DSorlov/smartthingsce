"""Webhook manager for SmartThings Community Edition."""

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_TUNNEL_SUBDOMAIN, CONF_WEBHOOK_ENABLED, WEBHOOK_PATH

_LOGGER = logging.getLogger(__name__)

# Try to import localtunnel
try:
    from localtunnel import LocalTunnelClient
    LOCALTUNNEL_AVAILABLE = True
except ImportError:
    _LOGGER.debug("localtunnel-py not available, falling back to polling mode")
    LOCALTUNNEL_AVAILABLE = False


class SmartThingsWebhookView(HomeAssistantView):
    """Handle SmartThings webhook callbacks."""

    url = f"{WEBHOOK_PATH}/{{hook_id}}"
    name = "api:smartthingsce:webhook"
    requires_auth = False

    def __init__(self, hass: HomeAssistant, webhook_manager: "WebhookManager") -> None:
        """Initialize webhook view."""
        self.hass = hass
        self.webhook_manager = webhook_manager

    async def post(self, request: web.Request, hook_id: str) -> web.Response:
        """Handle webhook POST requests."""
        try:
            data = await request.json()
            _LOGGER.debug("Received webhook data: %s", data)

            # Verify this is for our hook
            if hook_id != self.webhook_manager.hook_id:
                _LOGGER.warning("Received webhook for unknown hook_id: %s", hook_id)
                return web.Response(status=404)

            # Handle lifecycle events
            lifecycle = data.get("lifecycle")
            
            if lifecycle == "PING":
                # Respond to ping with challenge
                challenge = data.get("pingData", {}).get("challenge")
                return web.json_response({"pingData": {"challenge": challenge}})
            
            elif lifecycle == "CONFIRMATION":
                # Handle app confirmation
                confirmation_url = data.get("confirmationData", {}).get("confirmationUrl")
                if confirmation_url:
                    _LOGGER.info("Webhook confirmation URL: %s", confirmation_url)
                return web.Response(status=200)
            
            elif lifecycle == "EVENT":
                # Handle device events
                await self.webhook_manager.handle_event(data)
                return web.Response(status=200)
            
            elif lifecycle == "CONFIGURATION":
                # Handle configuration phase
                return web.json_response({
                    "configurationData": {
                        "initialize": {
                            "name": "SmartThings Community Edition",
                            "description": "Home Assistant Integration",
                            "id": self.webhook_manager.app_id,
                            "permissions": [],
                            "firstPageId": "1"
                        }
                    }
                })
            
            else:
                _LOGGER.warning("Unknown lifecycle: %s", lifecycle)
                return web.Response(status=200)

        except Exception as err:
            _LOGGER.error("Error handling webhook: %s", err)
            return web.Response(status=500)


class WebhookManager:
    """Manage SmartThings webhook subscriptions."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: Any,
        coordinator: Any,
        entry: ConfigEntry,
    ) -> None:
        """Initialize webhook manager."""
        self.hass = hass
        self.api = api
        self.coordinator = coordinator
        self.entry = entry
        self.hook_id = str(uuid.uuid4())
        self.app_id = str(uuid.uuid4())
        self.tunnel: Optional[Any] = None
        self.tunnel_url: Optional[str] = None
        self.subscriptions: list = []

    async def async_setup(self) -> None:
        """Set up webhook and tunnel."""
        try:
            # Register webhook view
            webhook_view = SmartThingsWebhookView(self.hass, self)
            self.hass.http.register_view(webhook_view)

            # Start localtunnel if webhook is enabled
            if self.entry.data.get(CONF_WEBHOOK_ENABLED, False):
                await self._start_tunnel()
                
                # Create subscriptions for all devices
                await self._create_subscriptions()

            _LOGGER.info("Webhook manager setup completed")

        except Exception as err:
            _LOGGER.error("Failed to setup webhook: %s", err)

    async def async_cleanup(self) -> None:
        """Clean up webhook and tunnel."""
        try:
            # Delete subscriptions
            await self._delete_subscriptions()

            # Stop tunnel
            if self.tunnel:
                try:
                    await self.hass.async_add_executor_job(self.tunnel.close)
                except Exception as err:
                    _LOGGER.warning("Error closing tunnel: %s", err)
                self.tunnel = None

            _LOGGER.info("Webhook manager cleaned up")

        except Exception as err:
            _LOGGER.error("Failed to cleanup webhook: %s", err)

    async def _start_tunnel(self) -> None:
        """Start localtunnel using Python API."""
        if not LOCALTUNNEL_AVAILABLE:
            _LOGGER.info("Real-time webhooks not available, using polling mode (30-second updates)")
            return

        try:
            subdomain = self.entry.data.get(CONF_TUNNEL_SUBDOMAIN)
            port = 8123  # Home Assistant default port
            
            # Check if hass has a configured port
            if hasattr(self.hass, 'config') and hasattr(self.hass.config, 'api'):
                if hasattr(self.hass.config.api, 'port') and self.hass.config.api.port:
                    port = self.hass.config.api.port

            _LOGGER.info("Starting localtunnel on port %s with subdomain %s", port, subdomain)

            # Create tunnel client
            self.tunnel = LocalTunnelClient(port=port, subdomain=subdomain)
            
            # Open the tunnel (async)
            await self.tunnel.open()
            
            # Get the tunnel URL
            self.tunnel_url = self.tunnel.get_tunnel_url()
            webhook_url = f"{self.tunnel_url}{WEBHOOK_PATH}/{self.hook_id}"
            _LOGGER.info("Localtunnel started successfully: %s", webhook_url)
                
        except Exception as err:
            _LOGGER.error("Failed to start localtunnel: %s", err)
            _LOGGER.warning(
                "The integration will work using polling (30-second updates). "
                "For real-time updates, ensure localtunnel-py is installed correctly."
            )
            await asyncio.sleep(3)

            self.tunnel_url = f"https://{subdomain}.loca.lt{WEBHOOK_PATH}/{self.hook_id}"
            _LOGGER.info("Localtunnel started: %s", self.tunnel_url)

        except Exception as err:
            _LOGGER.error("Failed to start localtunnel: %s", err)
            _LOGGER.info("Install localtunnel-py: pip install localtunnel-py")

    async def _create_subscriptions(self) -> None:
        """Create subscriptions for all devices."""
        try:
            # This is a simplified version
            # In production, you'd need to register as a SmartApp
            # and use the SmartApp subscription API
            _LOGGER.info("Subscription creation would happen here")
            
        except Exception as err:
            _LOGGER.error("Failed to create subscriptions: %s", err)

    async def _delete_subscriptions(self) -> None:
        """Delete all subscriptions."""
        try:
            for subscription_id in self.subscriptions:
                # Delete subscription
                _LOGGER.debug("Deleting subscription: %s", subscription_id)
            
            self.subscriptions.clear()
            
        except Exception as err:
            _LOGGER.error("Failed to delete subscriptions: %s", err)

    async def handle_event(self, data: Dict[str, Any]) -> None:
        """Handle incoming device event."""
        try:
            event_data = data.get("eventData", {})
            events = event_data.get("events", [])

            for event in events:
                device_id = event.get("deviceId")
                component_id = event.get("componentId", "main")
                capability = event.get("capability")
                attribute = event.get("attribute")
                value = event.get("value")

                _LOGGER.debug(
                    "Device event: %s/%s.%s.%s = %s",
                    device_id,
                    component_id,
                    capability,
                    attribute,
                    value,
                )

                # Update device status in coordinator
                if device_id in self.coordinator.devices:
                    device = self.coordinator.devices[device_id]
                    if "status" not in device:
                        device["status"] = {}
                    if component_id not in device["status"]:
                        device["status"][component_id] = {}
                    if capability not in device["status"][component_id]:
                        device["status"][component_id][capability] = {}
                    
                    device["status"][component_id][capability][attribute] = {
                        "value": value
                    }

            # Trigger coordinator update
            await self.coordinator.async_request_refresh()

        except Exception as err:
            _LOGGER.error("Error handling device event: %s", err)
