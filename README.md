# HealthSync HA

Home Assistant custom integration that accepts HealthKit data from the HealthSync HA iOS app via a webhook and exposes metrics as sensors.

## Setup

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=WeaveHubHQ&repository=healthsync-ha)

### Manual installation
1. In HACS → Integrations → Custom repositories, add `https://github.com/WeaveHubHQ/healthsync-ha` as type **Integration**.
2. Install the integration and choose the latest tagged release (e.g., `v0.1.3`).
3. Restart Home Assistant.
4. Add Integration → HealthSync HA. Copy the generated webhook URL into the iOS app.

## Payload example
```json
{"metric":"heart_rate","value":72,"unit":"count/min","timestamp":"2024-01-01T12:00:00Z","device":"jason-iphone"}
```

## Lovelace fitness cards (optional)
- Pair this integration with the Fitness Cards bundle for Apple Health-style dashboards: https://github.com/WeaveHubHQ/healthsync-ha-cards
- Cards cover activity, vitals, sleep, body metrics, workouts, and overview with presets and auto-detect.
- Example YAML (replace with your entities):
  ```yaml
  - type: custom:fitness-overview-card
    period: 7d
    history: true
    primary_metrics:
      - preset: active_energy
        entity: sensor.health_active_energy_burned_daily_total
      - preset: steps
        entity: sensor.health_steps_daily_total
      - preset: distance_walk_run
        entity: sensor.health_distance_walking_running_daily_total
      - preset: weight
        entity: sensor.health_weight
    secondary_metrics:
      - preset: heart_rate
        entity: sensor.health_heart_rate
      - preset: spo2
        entity: sensor.health_oxygen_saturation
      - preset: body_fat_percentage
        entity: sensor.health_body_fat_percentage
  ```

## Contributions

We welcome all contributions. Please fork the repository if you would like to contribute.

Come see our other apps and integrations at [WeaveHub](https://weavehub.app).
