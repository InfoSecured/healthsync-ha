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

from .const import DOMAIN, DEFAULT_METRIC_UNITS, signal_metric_update, signal_new_metric

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

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self.entry_id = entry_id
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

            _LOGGER.debug("Webhook payload received: %s", payload)
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
        value = payload.get("value")
        unit = payload.get("unit") or DEFAULT_METRIC_UNITS.get(metric, "")
        timestamp = payload.get("timestamp")
        device = payload.get("device")

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
