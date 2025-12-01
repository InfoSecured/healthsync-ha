"""Validation utilities for HealthSync HA metrics."""

from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Valid metric ranges (min, max) for numeric health data
METRIC_RANGES = {
    "connectivity_test": (0, 1),  # Test metric for webhook validation
    "heart_rate": (30, 250),
    "resting_heart_rate": (30, 150),
    "heart_rate_variability": (0, 300),  # legacy name
    "heart_rate_variability_sdnn": (0, 300),
    "respiratory_rate": (4, 60),
    "vo2_max": (10, 100),
    "blood_glucose": (20, 600),  # mg/dL
    "weight": (0.5, 700),  # kg
    "oxygen_saturation": (50, 100),  # percentage
    "active_energy_burned": (0, 10000),  # kcal
    "basal_energy_burned": (0, 5000),  # kcal
    "distance_walking_running": (0, 200),  # km
    "distance_cycling": (0, 500),  # km
    "flights_climbed": (0, 500),
    "body_fat_percentage": (1, 70),
    "lean_body_mass": (0.5, 300),  # kg
    "body_mass_index": (10, 70),  # legacy name
    "bmi": (10, 70),
    "basal_body_temperature": (30, 45),  # Celsius
    "hydration": (0, 20),  # L
    "environmental_sound_exposure": (0, 150),  # dB
    "blood_pressure_systolic": (50, 250),  # mmHg
    "blood_pressure_diastolic": (30, 150),  # mmHg
    "step_count": (0, 100000),  # legacy name
    "steps": (0, 100000),
}

# Valid units for each metric type
VALID_UNITS = {
    "connectivity_test": {"count"},
    "heart_rate": {"bpm", "beats/min"},
    "resting_heart_rate": {"bpm", "beats/min"},
    "heart_rate_variability": {"ms"},  # legacy name
    "heart_rate_variability_sdnn": {"ms"},
    "respiratory_rate": {"breaths/min"},
    "vo2_max": {"mL/(kg·min)", "mL/(kg*min)"},
    "blood_glucose": {"mg/dL", "mmol/L"},
    "weight": {"lb", "kg"},
    "oxygen_saturation": {"%"},
    "active_energy_burned": {"kcal", "kJ"},
    "basal_energy_burned": {"kcal", "kJ"},
    "distance_walking_running": {"mi", "km"},
    "distance_cycling": {"mi", "km"},
    "flights_climbed": {"count"},
    "body_fat_percentage": {"%"},
    "lean_body_mass": {"lb", "kg"},
    "body_mass_index": {"count"},  # legacy name
    "bmi": {"count", "bmi"},
    "basal_body_temperature": {"degF", "degC"},
    "hydration": {"fl_oz", "fl oz", "fl oz US", "L", "mL"},
    "environmental_sound_exposure": {"dB", "dBA"},
    "blood_pressure_systolic": {"mmHg"},
    "blood_pressure_diastolic": {"mmHg"},
    "step_count": {"count"},  # legacy name
    "steps": {"steps", "count"},
}

# Metrics that should always be present
ALLOWED_METRICS = set(METRIC_RANGES.keys())


def validate_metric_name(metric: str) -> tuple[bool, str | None]:
    """
    Validate metric name.

    Args:
        metric: The metric name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not metric:
        return False, "Metric name is empty"

    if not isinstance(metric, str):
        return False, "Metric name must be a string"

    # Check for reasonable length
    if len(metric) > 100:
        return False, "Metric name too long"

    # Check if metric is in allowed list (warn but don't reject for forward compatibility)
    if metric not in ALLOWED_METRICS:
        _LOGGER.warning("Unknown metric '%s' - allowing for forward compatibility", metric)

    return True, None


def validate_metric_value(metric: str, value: float) -> tuple[bool, str | None]:
    """
    Validate metric value is within reasonable range.

    Args:
        metric: The metric name
        value: The numeric value to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, (int, float)):
        return False, f"Value must be numeric, got {type(value).__name__}"

    # Check for NaN or infinity
    if value != value or abs(value) == float('inf'):  # NaN check
        return False, "Value cannot be NaN or infinity"

    # Check against known ranges
    if metric in METRIC_RANGES:
        min_val, max_val = METRIC_RANGES[metric]
        if value < min_val or value > max_val:
            return False, f"Value {value} outside valid range [{min_val}, {max_val}] for {metric}"

    return True, None


def validate_metric_unit(metric: str, unit: str) -> tuple[bool, str | None]:
    """
    Validate metric unit is appropriate for the metric type.

    Args:
        metric: The metric name
        unit: The unit string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not unit:
        return False, "Unit is empty"

    if not isinstance(unit, str):
        return False, "Unit must be a string"

    # Check against known valid units (warn but don't reject for forward compatibility)
    if metric in VALID_UNITS:
        valid_units = VALID_UNITS[metric]
        if unit not in valid_units:
            _LOGGER.warning(
                "Unusual unit '%s' for metric '%s', expected one of: %s",
                unit, metric, valid_units
            )

    return True, None


def validate_payload(payload: dict[str, Any]) -> tuple[bool, str | None]:
    """
    Validate a complete webhook payload.

    Args:
        payload: The payload dictionary to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    metric = payload.get("metric")
    if not metric:
        return False, "Missing required field: metric"

    # Validate metric name
    is_valid, error = validate_metric_name(metric)
    if not is_valid:
        return False, f"Invalid metric name: {error}"

    # Value is optional (some payloads might be status updates)
    value = payload.get("value")
    if value is not None:
        is_valid, error = validate_metric_value(metric, value)
        if not is_valid:
            return False, f"Invalid value: {error}"

    # Unit validation
    unit = payload.get("unit")
    if unit:
        is_valid, error = validate_metric_unit(metric, unit)
        if not is_valid:
            return False, f"Invalid unit: {error}"

    # Validate timestamp format if present (basic check)
    timestamp = payload.get("timestamp")
    if timestamp and not isinstance(timestamp, str):
        return False, "Timestamp must be a string"

    return True, None


def sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize payload by removing potentially dangerous fields and limiting sizes.

    Args:
        payload: The payload to sanitize

    Returns:
        Sanitized payload dictionary
    """
    sanitized = {}

    # Only copy known safe fields
    safe_fields = {"metric", "value", "unit", "timestamp", "device", "source"}

    for field in safe_fields:
        if field in payload:
            value = payload[field]

            # Limit string lengths
            if isinstance(value, str):
                sanitized[field] = value[:500]  # Max 500 chars
            elif isinstance(value, (int, float)):
                sanitized[field] = value
            # Skip other types

    return sanitized
