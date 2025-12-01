"""Webhook handling for the Apple HealthKit Bridge integration."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from typing import Any

from homeassistant.components import webhook
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    DOMAIN,
    DEFAULT_METRIC_UNITS,
    signal_metric_update,
    signal_new_metric,
    CONF_WEIGHT_UNIT,
    CONF_DISTANCE_UNIT,
    CONF_TEMPERATURE_UNIT,
    CONF_ENERGY_UNIT,
    CONF_HYDRATION_UNIT,
)

MAX_HISTORY = 10
_LOGGER = logging.getLogger(__name__)


@dataclass
class MetricState:
    """State container for a HealthKit metric."""

    value: float | int | str
    unit: str
    last_updated: datetime
    source_device: str | None = None
    samples: deque[float] = field(default_factory=lambda: deque(maxlen=MAX_HISTORY))

    def as_attributes(self) -> dict[str, Any]:
        values = list(self.samples)
        attrs: dict[str, Any] = {
            "last_updated": self.last_updated.isoformat(),
            "source_device": self.source_device,
        }
        if values:
            attrs["min"] = min(values)
            attrs["max"] = max(values)
            attrs["avg"] = sum(values) / len(values)
        return attrs


class AppleHealthManager:
    """Manage metric storage and webhook dispatch."""

    def __init__(self, hass: HomeAssistant, entry_id: str, options: dict[str, Any]) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.options = options
        self.metrics: dict[str, MetricState] = {}

    def register(self, webhook_id: str) -> None:
        """Register a webhook handler for this entry."""

        async def _handle_webhook(
            hass: HomeAssistant, _id: str, request
        ) -> webhook.WebhookResponse:
            try:
                payload = await request.json()
            except Exception as err:
                _LOGGER.warning("Webhook received non-JSON payload: %s", err)
                return webhook.WebhookResponse(
                    body="invalid json",
                    status=400,
                    headers={"Content-Type": "text/plain"},
                )

            _LOGGER.info("Webhook payload received: %s", payload)
            if isinstance(payload, list):
                for item in payload:
                    if isinstance(item, dict):
                        self._process_payload(item)
            elif isinstance(payload, dict):
                self._process_payload(payload)
            else:
                _LOGGER.warning("Webhook payload ignored (not dict/list): %s", type(payload))
            return webhook.WebhookResponse(
                body="ok", status=200, headers={"Content-Type": "text/plain"}
            )

        webhook.async_register(
            self.hass,
            DOMAIN,
            f"{DOMAIN}_{self.entry_id}",
            webhook_id,
            _handle_webhook,
        )
        _LOGGER.info("Registered HealthSync HA webhook id %s", webhook_id)

    def unregister(self, webhook_id: str) -> None:
        """Unregister the webhook."""
        webhook.async_unregister(self.hass, webhook_id)
        _LOGGER.info("Unregistered HealthSync HA webhook id %s", webhook_id)

    def _process_payload(self, payload: dict[str, Any]) -> None:
        """Validate and dispatch incoming payload."""
        metric = payload.get("metric")
        if not metric:
            _LOGGER.warning("Webhook payload missing 'metric': %s", payload)
            return
        if metric == "body_mass":
            metric = "weight"
        value = payload.get("value")
        unit = payload.get("unit") or DEFAULT_METRIC_UNITS.get(metric, "")
        timestamp = payload.get("timestamp")
        device = payload.get("device")

        value, unit = self._convert_units(metric, value, unit)

        try:
            ts = (
                datetime.fromisoformat(timestamp)
                if isinstance(timestamp, str)
                else datetime.now(timezone.utc)
            )
        except (TypeError, ValueError):
            ts = datetime.now(timezone.utc)

        state = self.metrics.get(metric)
        if state is None:
            state = MetricState(value=value, unit=unit, last_updated=ts, source_device=device)
            if isinstance(value, (int, float)):
                state.samples.append(float(value))
            self.metrics[metric] = state
            async_dispatcher_send(self.hass, signal_new_metric(self.entry_id), metric)
        else:
            state.value = value
            state.unit = unit
            state.last_updated = ts
            state.source_device = device or state.source_device
            if isinstance(value, (int, float)):
                state.samples.append(float(value))
        async_dispatcher_send(self.hass, signal_metric_update(self.entry_id), metric)

    def _convert_units(self, metric: str, value: Any, unit: str) -> tuple[Any, str]:
        """Convert incoming value/unit to user-selected units."""
        if not isinstance(value, (int, float)):
            return value, unit
        opts = self.options or {}
        target_unit = None
        if metric in ("weight", "lean_body_mass"):
            target_unit = opts.get(CONF_WEIGHT_UNIT)
            if target_unit == "kg" and unit == "lb":
                return value * 0.45359237, "kg"
            if target_unit == "lb" and unit == "kg":
                return value / 0.45359237, "lb"
        elif metric in ("distance_walking_running", "distance_cycling"):
            target_unit = opts.get(CONF_DISTANCE_UNIT)
            if target_unit == "km" and unit == "mi":
                return value * 1.60934, "km"
            if target_unit == "mi" and unit == "km":
                return value / 1.60934, "mi"
        elif metric == "basal_body_temperature":
            target_unit = opts.get(CONF_TEMPERATURE_UNIT)
            if target_unit == "degC" and unit.lower().startswith("degf"):
                return (value - 32) / 1.8, "degC"
            if target_unit == "degF" and unit.lower().startswith("degc"):
                return (value * 1.8) + 32, "degF"
        elif metric in ("active_energy_burned", "basal_energy_burned"):
            target_unit = opts.get(CONF_ENERGY_UNIT)
            if target_unit == "kJ" and unit == "kcal":
                return value * 4.184, "kJ"
            if target_unit == "kcal" and unit == "kJ":
                return value / 4.184, "kcal"
        elif metric == "hydration":
            target_unit = opts.get(CONF_HYDRATION_UNIT)
            if target_unit == "L" and unit in ("fl oz", "fl_oz", "fl oz US"):
                return value * 0.0295735, "L"
            if target_unit == "fl_oz" and unit in ("L", "l"):
                return value / 0.0295735, "fl oz"
        return value, unit
