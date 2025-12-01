"""Config flow for Apple HealthKit Bridge."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.components.webhook import async_generate_id

from .const import (
    CONF_DEVICE_ID,
    CONF_NAME,
    CONF_WEBHOOK_ID,
    DOMAIN,
    CONF_WEIGHT_UNIT,
    CONF_DISTANCE_UNIT,
    CONF_TEMPERATURE_UNIT,
    CONF_ENERGY_UNIT,
    CONF_HYDRATION_UNIT,
    DEFAULT_OPTIONS_METRIC,
)


class AppleHealthKitConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Apple HealthKit Bridge."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return AppleHealthKitOptionsFlowHandler(config_entry)
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
                options=self._initial_options(),
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

    def _initial_options(self) -> dict:
        is_metric = self.hass.config.units.is_metric
        defaults = DEFAULT_OPTIONS_METRIC.copy()
        if is_metric:
            defaults[CONF_WEIGHT_UNIT] = "kg"
            defaults[CONF_DISTANCE_UNIT] = "km"
            defaults[CONF_TEMPERATURE_UNIT] = "degC"
            defaults[CONF_ENERGY_UNIT] = "kJ"
            defaults[CONF_HYDRATION_UNIT] = "L"
        return defaults


class AppleHealthKitOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for unit preferences."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Preserve webhook id even if user edits it in options (not recommended).
            merged = {**opts, **user_input}
            if CONF_WEBHOOK_ID not in merged and CONF_WEBHOOK_ID in self.config_entry.data:
                merged[CONF_WEBHOOK_ID] = self.config_entry.data[CONF_WEBHOOK_ID]
            return self.async_create_entry(title="", data=merged)

        opts = {**DEFAULT_OPTIONS_METRIC, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_WEBHOOK_ID, description={"suggested_value": self.config_entry.data.get(CONF_WEBHOOK_ID, "")}): cv.string,
                    vol.Required(CONF_WEIGHT_UNIT, default=opts[CONF_WEIGHT_UNIT]): vol.In(
                        ["lb", "kg"]
                    ),
                    vol.Required(
                        CONF_DISTANCE_UNIT, default=opts[CONF_DISTANCE_UNIT]
                    ): vol.In(["mi", "km"]),
                    vol.Required(
                        CONF_TEMPERATURE_UNIT, default=opts[CONF_TEMPERATURE_UNIT]
                    ): vol.In(["degF", "degC"]),
                    vol.Required(CONF_ENERGY_UNIT, default=opts[CONF_ENERGY_UNIT]): vol.In(
                        ["kcal", "kJ"]
                    ),
                    vol.Required(
                        CONF_HYDRATION_UNIT, default=opts[CONF_HYDRATION_UNIT]
                    ): vol.In(["fl_oz", "L"]),
                }
            ),
        )
