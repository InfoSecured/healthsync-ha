"""Sensor platform for Apple HealthKit Bridge."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    CONF_WEBHOOK_ID,
    DEFAULT_METRIC_UNITS,
    DOMAIN,
    signal_metric_update,
    signal_new_metric,
)
from .webhook import AppleHealthManager, MetricState


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up sensors for a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    manager: AppleHealthManager = data["manager"]

    entities = [
        AppleHealthMetricSensor(entry, manager, metric) for metric in manager.metrics
    ]
    async_add_entities(entities)

    @callback
    def _add_metric(metric: str) -> None:
        async_add_entities([AppleHealthMetricSensor(entry, manager, metric)])

    manager_unsub = async_dispatcher_connect(
        hass, signal_new_metric(entry.entry_id), _add_metric
    )
    data["manager_unsub"] = manager_unsub


class AppleHealthMetricSensor(SensorEntity):
    """A sensor representing a single HealthKit metric."""

    _attr_should_poll = False

    def __init__(
        self, entry: ConfigEntry, manager: AppleHealthManager, metric: str
    ) -> None:
        self.entry = entry
        self.manager = manager
        self.metric = metric
        self._attr_unique_id = f"{entry.entry_id}_{metric}"
        friendly_metric = metric.replace("_", " ").title()
        self._attr_name = f"{entry.title} {friendly_metric}"
        self._unit = DEFAULT_METRIC_UNITS.get(metric, None)
        self._unsub = None

    async def async_added_to_hass(self) -> None:
        """Register dispatcher callbacks."""
        self._unsub = async_dispatcher_connect(
            self.hass,
            signal_metric_update(self.entry.entry_id),
            self._handle_update,
        )
        # Publish the initial state so the first sample is visible immediately.
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up listeners."""
        if self._unsub:
            self._unsub()

    @property
    def native_value(self) -> Any:
        state = self._state
        return None if state is None else state.value

    @property
    def native_unit_of_measurement(self) -> str | None:
        state = self._state
        return state.unit if state else self._unit

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        state = self._state
        return state.as_attributes() if state else {}

    @property
    def _state(self) -> MetricState | None:
        return self.manager.metrics.get(self.metric)

    @callback
    def _handle_update(self, metric: str) -> None:
        if metric != self.metric:
            return
        self.async_write_ha_state()
