"""Constants for the Apple HealthKit Bridge integration."""

DOMAIN = "healthsync_ha"
PLATFORMS: list[str] = ["sensor"]

CONF_NAME = "name"
CONF_DEVICE_ID = "device_id"
CONF_WEBHOOK_ID = "webhook_id"

# Default set of supported metrics and their native units.
DEFAULT_METRIC_UNITS = {
    "steps": "steps",
    "heart_rate": "bpm",
    "sleep": "hours",
    "blood_glucose": "mg/dL",
    "body_mass": "kg",
    "weight": "kg",
    "oxygen_saturation": "%",
}

# Dispatcher signal builders.
def signal_new_metric(entry_id: str) -> str:
    return f"{DOMAIN}_{entry_id}_new_metric"


def signal_metric_update(entry_id: str) -> str:
    return f"{DOMAIN}_{entry_id}_metric_update"
