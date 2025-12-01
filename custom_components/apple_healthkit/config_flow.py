"""Config flow for Apple HealthKit Bridge."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.components.webhook import async_generate_id

from .const import CONF_DEVICE_ID, CONF_NAME, CONF_WEBHOOK_ID, DOMAIN


class AppleHealthKitConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Apple HealthKit Bridge."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            device_id = user_input.get(CONF_DEVICE_ID) or ""
            webhook_id = async_generate_id()
            await self.async_set_unique_id(webhook_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=name,
                data={
                    CONF_NAME: name,
                    CONF_DEVICE_ID: device_id,
                    CONF_WEBHOOK_ID: webhook_id,
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): cv.string,
                vol.Optional(CONF_DEVICE_ID, default=""): cv.string,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "hint": "Home Assistant will generate a webhook ID and URL."
            },
        )
