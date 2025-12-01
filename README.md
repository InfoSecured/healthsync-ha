# HealthSync HA

Home Assistant custom integration that accepts HealthKit data from the HealthSync HA iOS app via a webhook and exposes metrics as sensors.

## Installation (HACS)
1. In HACS → Integrations → Custom repositories, add `https://github.com/InfoSecured/healthsync-ha` as type **Integration**.
2. Install the integration and choose the latest tagged release (e.g., `v0.1.2`).
3. Restart Home Assistant.
4. Add Integration → HealthSync HA. Copy the generated webhook URL into the iOS app.

## Manual install
- Copy `custom_components/apple_healthkit/` into your Home Assistant `custom_components/` directory.
- Restart Home Assistant and add the integration.

## Payload example
```json
{"metric":"heart_rate","value":72,"unit":"count/min","timestamp":"2024-01-01T12:00:00Z","device":"jason-iphone"}
```

## Versioning
Tagged releases follow semantic versioning. HACS requires installing from a tagged release, not from a raw commit.
