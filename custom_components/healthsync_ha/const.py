"""Constants for the Apple HealthKit Bridge integration."""

DOMAIN = "healthsync_ha"
PLATFORMS: list[str] = ["sensor"]

CONF_NAME = "name"
CONF_DEVICE_ID = "device_id"
CONF_WEBHOOK_ID = "webhook_id"
CONF_WEIGHT_UNIT = "weight_unit"
CONF_DISTANCE_UNIT = "distance_unit"
CONF_TEMPERATURE_UNIT = "temperature_unit"
CONF_ENERGY_UNIT = "energy_unit"
CONF_HYDRATION_UNIT = "hydration_unit"

# Default set of supported metrics and their native units.
DEFAULT_METRIC_UNITS = {
    "steps": "steps",
    "heart_rate": "bpm",
    "resting_heart_rate": "bpm",
    "heart_rate_variability_sdnn": "ms",
    "respiratory_rate": "breaths/min",
    "vo2_max": "mL/(kg*min)",
    "sleep": "hours",
    "blood_glucose": "mg/dL",
    "body_mass": "kg",
    "weight": "lb",
    "body_fat_percentage": "%",
    "lean_body_mass": "lb",
    "bmi": "bmi",
    "oxygen_saturation": "%",
    "active_energy_burned": "kcal",
    "basal_energy_burned": "kcal",
    "distance_walking_running": "mi",
    "distance_cycling": "mi",
    "flights_climbed": "count",
    "basal_body_temperature": "degF",
    "hydration": "fl oz",
    "environmental_sound_exposure": "dBA",
    "blood_pressure_systolic": "mmHg",
    "blood_pressure_diastolic": "mmHg",
}

# Dispatcher signal builders.
def signal_new_metric(entry_id: str) -> str:
    return f"{DOMAIN}_{entry_id}_new_metric"


def signal_metric_update(entry_id: str) -> str:
    return f"{DOMAIN}_{entry_id}_metric_update"


DEFAULT_OPTIONS_METRIC = {
    CONF_WEIGHT_UNIT: "lb",
    CONF_DISTANCE_UNIT: "mi",
    CONF_TEMPERATURE_UNIT: "degF",
    CONF_ENERGY_UNIT: "kcal",
    CONF_HYDRATION_UNIT: "fl_oz",
}
