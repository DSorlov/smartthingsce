"""Config flow for SmartThings Community Edition."""

import logging
import uuid
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_LOCATION_ID,
    CONF_TUNNEL_SUBDOMAIN,
    CONF_WEBHOOK_ENABLED,
    DOMAIN,
    ERROR_AUTH_FAILED,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_TOKEN,
    ERROR_NO_LOCATIONS,
    ERROR_UNKNOWN,
)
from .smartthings_api import SmartThingsAPI, SmartThingsAPIError

_LOGGER = logging.getLogger(__name__)


class SmartThingsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SmartThings Community Edition."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._access_token: Optional[str] = None
        self._locations: list = []
        self._location_id: Optional[str] = None

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Strip whitespace from token
            self._access_token = user_input[CONF_ACCESS_TOKEN].strip()

            # Validate token and get locations
            try:
                session = async_get_clientsession(self.hass)
                api = SmartThingsAPI(self._access_token, session)

                _LOGGER.debug("Attempting to validate token and fetch locations")
                self._locations = await api.get_locations()
                _LOGGER.debug("Successfully fetched %d locations", len(self._locations))

                if not self._locations:
                    errors["base"] = ERROR_NO_LOCATIONS
                else:
                    return await self.async_step_location()

            except SmartThingsAPIError as err:
                _LOGGER.error("SmartThings API error: %s", err)
                errors["base"] = ERROR_AUTH_FAILED
            except Exception as err:
                _LOGGER.exception(
                    "Unexpected exception during token validation: %s", err
                )
                errors["base"] = ERROR_UNKNOWN

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ACCESS_TOKEN): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "token_url": "https://account.smartthings.com/tokens"
            },
        )

    async def async_step_location(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle location selection."""
        if user_input is not None:
            self._location_id = user_input[CONF_LOCATION_ID]
            return await self.async_step_webhook()

        # Create location selection schema
        location_options = {loc["locationId"]: loc["name"] for loc in self._locations}

        data_schema = vol.Schema(
            {
                vol.Required(CONF_LOCATION_ID): vol.In(location_options),
            }
        )

        return self.async_show_form(
            step_id="location",
            data_schema=data_schema,
        )

    async def async_step_webhook(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle webhook configuration."""
        if user_input is not None:
            webhook_enabled = user_input.get(CONF_WEBHOOK_ENABLED, False)

            # Generate unique tunnel subdomain
            unique_id = str(uuid.uuid4())[:8]
            integration_id = str(uuid.uuid4())[:8]
            tunnel_subdomain = f"{unique_id}-{integration_id}-stce"

            # Create the config entry
            title = next(
                (
                    loc["name"]
                    for loc in self._locations
                    if loc["locationId"] == self._location_id
                ),
                "SmartThings",
            )

            await self.async_set_unique_id(f"{DOMAIN}_{self._location_id}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=title,
                data={
                    CONF_ACCESS_TOKEN: self._access_token,
                    CONF_LOCATION_ID: self._location_id,
                    CONF_WEBHOOK_ENABLED: webhook_enabled,
                    CONF_TUNNEL_SUBDOMAIN: tunnel_subdomain,
                },
            )

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_WEBHOOK_ENABLED, default=True): bool,
            }
        )

        return self.async_show_form(
            step_id="webhook",
            data_schema=data_schema,
            description_placeholders={
                "location_name": next(
                    (
                        loc["name"]
                        for loc in self._locations
                        if loc["locationId"] == self._location_id
                    ),
                    "Unknown",
                )
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return SmartThingsOptionsFlow(config_entry)


class SmartThingsOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for SmartThings Community Edition."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Manage the options."""
        if user_input is not None:
            # Update config entry data instead of options
            new_data = {**self.config_entry.data}
            new_data[CONF_WEBHOOK_ENABLED] = user_input.get(CONF_WEBHOOK_ENABLED, False)

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )

            return self.async_create_entry(title="", data={})

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_WEBHOOK_ENABLED,
                    default=self.config_entry.data.get(CONF_WEBHOOK_ENABLED, False),
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
