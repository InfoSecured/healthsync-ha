# HealthSync HA (Home Assistant)

This custom integration accepts data from the **HealthSync HA** iOS app (or any client) via a Home Assistant webhook and exposes metrics as sensors.

## Install
1. Copy `custom_components/apple_healthkit/` into your Home Assistant config directory.
2. Restart Home Assistant.
3. Add Integration → “HealthSync HA”.

## Config Flow
- Provide a friendly name (e.g., “Jason’s iPhone Health”).
- The flow generates a webhook ID and shows the URL: `https://<ha>/api/webhook/<id>`.
- Paste that URL into the iOS app. No additional token is required for the webhook path.

## Payload Format
Send either a single object or an array:
```json
{"metric":"heart_rate","value":72,"unit":"count/min","timestamp":"2024-01-01T12:00:00Z","device":"jason-iphone"}
```
Supported metrics map to sensor IDs like `sensor.apple_health_steps` and use the Home Assistant entity registry to persist names.

## Entities & Attributes
- Sensors are created on-demand per metric received.
- Attributes include `last_updated`, `source_device`, and rolling `min`/`max`/`avg` over the last few samples.

## Optional MQTT
If you prefer MQTT, point the iOS app to publish `health/<device>/<metric>` payloads. Extend the integration by subscribing to those topics or bridging MQTT to webhook with an HA automation.

## Versioning
- Semantic Versioning: MAJOR when payload/entity behavior changes incompatibly, MINOR when adding metrics or capabilities, PATCH for fixes. Update `manifest.json` and tag releases accordingly.
- Tag helper: run `scripts/tag_release.sh <version>` from repo root after merging to main; then `git push origin v<version>`.
