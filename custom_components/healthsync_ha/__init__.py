"""Set up the Apple HealthKit Bridge integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components import persistent_notification

from .const import DOMAIN, PLATFORMS, CONF_WEBHOOK_ID, DEFAULT_OPTIONS_METRIC
from .webhook import AppleHealthManager


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up via YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Apple HealthKit Bridge from a config entry."""
    manager = AppleHealthManager(hass, entry.entry_id, entry.options or DEFAULT_OPTIONS_METRIC)
    manager.register(entry.data[CONF_WEBHOOK_ID])

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "manager": manager,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Surface the webhook ID so users can copy it easily.
    persistent_notification.async_create(
        hass,
        f"HealthSync HA Webhook ID: `{entry.data[CONF_WEBHOOK_ID]}`\n\n"
        "Use it with your Home Assistant base URL: `/api/webhook/<ID>`.",
        title=entry.title or "HealthSync HA",
        notification_id=f"{DOMAIN}_{entry.entry_id}_webhook",
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    manager: AppleHealthManager = hass.data[DOMAIN][entry.entry_id]["manager"]
    manager.unregister(entry.data[CONF_WEBHOOK_ID])

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        unsub = hass.data[DOMAIN][entry.entry_id].get("manager_unsub")
        if unsub:
            unsub()
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
