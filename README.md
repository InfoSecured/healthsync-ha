# HealthSync HA

Home Assistant custom integration that accepts HealthKit data from the HealthSync HA iOS app via a webhook and exposes metrics as sensors.

## Installation (HACS)
1. In HACS → Integrations → Custom repositories, add `https://github.com/WeaveHubHQ/healthsync-ha` as type **Integration**.
2. Install the integration and choose the latest tagged release (e.g., `v0.1.3`).
3. Restart Home Assistant.
4. Add Integration → HealthSync HA. Copy the generated webhook URL into the iOS app.

## Manual install
- Copy `custom_components/healthsync_ha/` into your Home Assistant `custom_components/` directory.
- Restart Home Assistant and add the integration.

## Payload example
```json
{"metric":"heart_rate","value":72,"unit":"count/min","timestamp":"2024-01-01T12:00:00Z","device":"jason-iphone"}
```

## Contributions

We welcome all contributions. Please fork the repository if you would like to contribute.

Come see our other apps and integrations at [WeaveHub](https://weavehub.app).
