"""Sensor platform for Apple HealthKit Bridge."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo

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
        # Listen for metric-specific updates (more efficient than global signal)
        self._unsub = async_dispatcher_connect(
            self.hass,
            signal_metric_update(self.entry.entry_id, self.metric),
            self._handle_update,
        )
        _LOGGER.info("Sensor added: %s (%s)", self.metric, self.unique_id)
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
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class for this sensor."""
        # Only use device classes that exist in Home Assistant
        device_class_map = {
            "basal_body_temperature": SensorDeviceClass.TEMPERATURE,
            "weight": SensorDeviceClass.WEIGHT,
            "lean_body_mass": SensorDeviceClass.WEIGHT,
            "distance_walking_running": SensorDeviceClass.DISTANCE,
            "distance_cycling": SensorDeviceClass.DISTANCE,
        }
        return device_class_map.get(self.metric)

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return the state class for this sensor."""
        # Most health metrics are measurements
        if self.metric in (
            "heart_rate",
            "resting_heart_rate",
            "heart_rate_variability_sdnn",
            "respiratory_rate",
            "vo2_max",
            "blood_glucose",
            "weight",
            "oxygen_saturation",
            "body_fat_percentage",
            "lean_body_mass",
            "bmi",
            "basal_body_temperature",
            "environmental_sound_exposure",
            "blood_pressure_systolic",
            "blood_pressure_diastolic",
            "active_energy_burned",
            "basal_energy_burned",
        ):
            return SensorStateClass.MEASUREMENT

        # Metrics like steps/distance can reset (per-day buckets in HealthKit), so
        # report them as measurements to avoid HA's total_increasing monotonicity errors.
        if self.metric in (
            "steps",
            "distance_walking_running",
            "distance_cycling",
            "flights_climbed",
            "hydration",
        ):
            return SensorStateClass.MEASUREMENT

        return None

    @property
    def icon(self) -> str | None:
        """Return the icon for this sensor."""
        icon_map = {
            "heart_rate": "mdi:heart-pulse",
            "resting_heart_rate": "mdi:heart",
            "heart_rate_variability_sdnn": "mdi:heart-flash",
            "respiratory_rate": "mdi:lungs",
            "vo2_max": "mdi:run",
            "blood_glucose": "mdi:diabetes",
            "weight": "mdi:scale-bathroom",
            "oxygen_saturation": "mdi:water-percent",
            "active_energy_burned": "mdi:fire",
            "basal_energy_burned": "mdi:fire-circle",
            "distance_walking_running": "mdi:walk",
            "distance_cycling": "mdi:bike",
            "flights_climbed": "mdi:stairs-up",
            "body_fat_percentage": "mdi:percent",
            "lean_body_mass": "mdi:human",
            "bmi": "mdi:human-male-height",
            "basal_body_temperature": "mdi:thermometer",
            "hydration": "mdi:cup-water",
            "environmental_sound_exposure": "mdi:volume-high",
            "blood_pressure_systolic": "mdi:heart-cog",
            "blood_pressure_diastolic": "mdi:heart-cog",
            "steps": "mdi:shoe-print",
        }
        return icon_map.get(self.metric)

    @property
    def suggested_display_precision(self) -> int | None:
        """Return the suggested display precision for this sensor."""
        # No decimals for counts
        if self.metric in ("steps", "flights_climbed"):
            return 0
        # One decimal for most measurements
        if self.metric in (
            "heart_rate",
            "resting_heart_rate",
            "weight",
            "bmi",
            "basal_body_temperature",
        ):
            return 1
        # Two decimals for precise measurements
        if self.metric in (
            "distance_walking_running",
            "distance_cycling",
            "body_fat_percentage",
        ):
            return 2
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to link sensors together."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.entry.title,
            manufacturer="HealthSync",
            model="iOS App",
            sw_version="1.0",
        )

    @property
    def _state(self) -> MetricState | None:
        return self.manager.metrics.get(self.metric)

    @callback
    def _handle_update(self) -> None:
        """Handle metric update signal (metric-specific, no filtering needed)."""
        _LOGGER.info(
            "Writing state metric=%s value=%s unit=%s ts=%s",
            self.metric,
            getattr(self._state, "value", None),
            getattr(self._state, "unit", None),
            getattr(self._state, "last_updated", None),
        )
        self.async_write_ha_state()
