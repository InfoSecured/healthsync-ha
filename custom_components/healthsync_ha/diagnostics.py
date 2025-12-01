"""Diagnostics support for HealthSync HA."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .webhook import AppleHealthManager


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    manager: AppleHealthManager = data["manager"]

    # Collect diagnostics data
    diagnostics = {
        "entry": {
            "title": entry.title,
            "entry_id": entry.entry_id,
            "version": entry.version,
            "domain": entry.domain,
        },
        "options": {
            "weight_unit": entry.options.get("weight_unit", "N/A"),
            "distance_unit": entry.options.get("distance_unit", "N/A"),
            "temperature_unit": entry.options.get("temperature_unit", "N/A"),
            "energy_unit": entry.options.get("energy_unit", "N/A"),
            "hydration_unit": entry.options.get("hydration_unit", "N/A"),
        },
        "metrics": {},
        "statistics": {
            "total_metrics": len(manager.metrics),
            "metrics_with_data": sum(
                1 for state in manager.metrics.values() if state.samples
            ),
        },
    }

    # Add metric information (without sensitive data)
    for metric_name, state in manager.metrics.items():
        diagnostics["metrics"][metric_name] = {
            "unit": state.unit,
            "last_updated": state.last_updated.isoformat() if state.last_updated else None,
            "sample_count": len(state.samples),
            "has_device": state.source_device is not None,
        }

        # Add min/max/avg if samples exist (for debugging)
        if state.samples:
            values = list(state.samples)
            diagnostics["metrics"][metric_name]["sample_stats"] = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "latest": values[-1] if values else None,
            }

    return diagnostics
