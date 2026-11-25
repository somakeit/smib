# SMIB Configuration Settings

This document provides a comprehensive overview of all configurable settings in S.M.I.B.

## Slack Settings

| Environment Variable | Description | Example | Default |
|---------------------|-------------|---------|---------|
| SMIB_SLACK_BOT_TOKEN | Slack bot token used for authentication with the Slack API | `xoxb-123456789012-1234567890123-abcdefghijklmnopqrstuvwx` | None (Required) |
| SMIB_SLACK_APP_TOKEN | Slack app token used for socket mode connections | `xapp-1-A1234567890-1234567890123-abcdefghijklmnopqrstuvwxyz1234567890123456789012` | None (Required) |
| SMIB_SLACK_SIGNING_SECRET | Secret used to verify requests from Slack | `abcdef1234567890abcdef1234567890` | Random generated string |

## Environment Settings

| Environment Variable      | Description                                                    | Example       | Default |
|---------------------------|----------------------------------------------------------------|---------------|---------|
| SMIB_ENVIRONMENT          | The application environment (PRODUCTION, TESTING, DEVELOPMENT) | `DEVELOPMENT` | `PRODUCTION` |

## General Settings

| Environment Variable | Description | Example | Default |
|---------------------|-------------|---------|---------|
| SMIB_TIMEZONE | Application timezone used for local date/time calculations. If unset, the standard `TZ` environment variable is used when available. | `Europe/London` | `TZ`, otherwise `Etc/UTC` |

## Database Settings

| Environment Variable | Description | Example | Default |
|---------------------|-------------|---------|---------|
| SMIB_DB_MONGO_DB_HOST | MongoDB server hostname or IP address | `mongodb.example.com` | `localhost` |
| SMIB_DB_MONGO_DB_PORT | MongoDB server port number | `27018` | `27017` |
| SMIB_DB_MONGO_DB_NAME | MongoDB database name, defaults to the project name | `smib-production` | Project name |

## Webserver Settings

| Environment Variable | Description                                                        | Example | Default |
|---------------------|--------------------------------------------------------------------|---------|---------|
| SMIB_WEBSERVER_HOST | Host address to bind the webserver to (0.0.0.0 for all interfaces) | `127.0.0.1` | `0.0.0.0` |
| SMIB_WEBSERVER_PORT | Port number for the webserver to listen on                         | `8080` | `80` |
| SMIB_WEBSERVER_PATH_PREFIX | URL path prefix for the webserver endpoints                        | `/smib/` | `/` |
| SMIB_WEBSERVER_FORWARDED_ALLOW_IPS | List of IPs allowed for X-Forwarded-For headers (* for all)        | `[10.0.0.1, 192.168.1.1]` | `[*]` |
| SMIB_WEBSERVER_LOG_REQUEST_DETAILS | Whether to log detailed information about HTTP requests            | `true` | `false` |

## Logging Settings
| Environment Variable | Description | Example | Default |
|---------------------|-------------|---------|---------|
| SMIB_LOGGING_LOG_LEVEL | Logging level for the application (DEBUG, INFO, WARNING, ERROR) | `DEBUG` | `INFO` |

## Docker Compose Settings

| Environment Variable | Description | Example | Default |
|---------------------|-------------|---------|---------|
| SMIB_COMPOSE_MONGO_DB_TAG | MongoDB container version tag | `4.4.18` | `latest` |
| SMIB_COMPOSE_ME_MONGO_DB_URL | MongoDB connection URL for Mongo Express | `mongodb://username:password@smib-db:27017/` | `mongodb://smib-db:27017/` |

## Proxy Settings

| Environment Variable | Description | Example | Default |
|---------------------|-------------|---------|---------|
| SMIB_PROXY_EXTERNAL_PORT | External port for the Traefik proxy | `8080` | `80` |
| SMIB_PROXY_TRUSTED_PROXIES | Trusted IPs for forwarded headers in Traefik | `10.0.0.1,192.168.1.1` | None |

## Plugin Settings

### Space State Plugin

| Environment Variable | Description | Example | Default |
|---------------------|-------------|---------|---------|
| SMIB_PLUGIN_SPACE_STATE_SPACE_OPEN_ANNOUNCE_CHANNEL_ID | Slack channel ID where space open/close announcements are posted | `C1234567890` | `space-open-announce` |

### Static Files Plugin

| Environment Variable | Description | Example | Default |
|---------------------|-------------|---------|---------|
| SMIB_PLUGIN_STATIC_FILES_STATIC_FILES_DIRECTORY | Directory path where static files are stored and served from | `public/assets` | `static` |

### S.M.I.B.H.I.D. Devices

Shared per-device settings, used by both `/howfresh` and the App Home light state, so a device
named "Clean Room" in one readout is not a bare hostname in the other.

| Environment Variable | Description | Example | Default |
|---------------------|-------------|---------|---------|
| SMIB_PLUGIN_SMIBHID_DEVICES_STALE_AFTER | Readings older than this are still shown, but marked as possibly stale. Accepts seconds (int), `HH:MM:SS`, or ISO8601 durations. Defaults to the same hour as the sensor log monitor's alert threshold. | `PT1H` or `1:00:00` or `3600` | `1:00:00` |
| SMIB_PLUGIN_SMIBHID_DEVICES_EXCLUDE_AFTER | Readings older than this are left out of the readout entirely. A device is only dropped while another is still reporting — if every device is this stale they are all shown and marked. Set to `None` to never drop a device. | `P2D` or `2 days, 0:00:00` or `172800` | `2 days, 0:00:00` |

Per-device overrides are keyed on the device hostname. A device needs an entry only to override
something; devices with no entry use the defaults above. Hostname keys are matched case
insensitively, and hyphens and underscores are interchangeable, so `SMIBHID-FAN` is
configured as `SMIBHID_FAN`.

| Environment Variable | Description | Example | Default |
|---------------------|-------------|---------|---------|
| SMIB_PLUGIN_SMIBHID_DEVICES_DEVICE__&lt;HOSTNAME&gt;__NAME | Friendly name shown instead of the device hostname | `Clean Room` | The device hostname |
| SMIB_PLUGIN_SMIBHID_DEVICES_DEVICE__&lt;HOSTNAME&gt;__ORDER | Position in a multi-device readout, lowest first. Devices without an order follow those that have one, sorted by name. | `1` | None |
| SMIB_PLUGIN_SMIBHID_DEVICES_DEVICE__&lt;HOSTNAME&gt;__STALE_AFTER | Overrides `STALE_AFTER` for this device. Useful when a device reports on a slower cadence than the rest. | `PT3H` or `3:00:00` | Plugin-wide `STALE_AFTER` |
| SMIB_PLUGIN_SMIBHID_DEVICES_DEVICE__&lt;HOSTNAME&gt;__EXCLUDE_AFTER | Overrides `EXCLUDE_AFTER` for this device | `P7D` | Plugin-wide `EXCLUDE_AFTER` |

For example, giving the two devices in the space friendly names:

```dotenv
SMIB_PLUGIN_SMIBHID_DEVICES_DEVICE__SMIBHID_FAN__NAME=Clean Room
SMIB_PLUGIN_SMIBHID_DEVICES_DEVICE__SMIBHID_FAN__ORDER=1
SMIB_PLUGIN_SMIBHID_DEVICES_DEVICE__SMIBHID_WORKSHOP__NAME=Workshop
SMIB_PLUGIN_SMIBHID_DEVICES_DEVICE__SMIBHID_WORKSHOP__ORDER=2
```

Without an `ORDER`, devices are ordered by display name. They are never ordered by how
recently they reported, which would make them swap places between renders.

`SMIBHID-FAN` is in the clean room — the hostname describes the relay it drives rather than
where it sits, which is the main reason to configure a name at all.

Only add `STALE_AFTER` or `EXCLUDE_AFTER` for a device that reports on a different cadence to
the rest — for example a battery-powered unit that only pushes hourly, where the default
one-hour threshold would flag it constantly:

```dotenv
SMIB_PLUGIN_SMIBHID_DEVICES_DEVICE__SMIBHID_SPARE__STALE_AFTER=PT3H
SMIB_PLUGIN_SMIBHID_DEVICES_DEVICE__SMIBHID_SPARE__EXCLUDE_AFTER=P7D
```

### S.M.I.B.H.I.D. Plugin
| Environment Variable | Description | Example | Default |
|---------------------|-------------|---------|---------|
| SMIB_PLUGIN_SMIBHID_SENSOR_MONITOR_INTERVAL | Interval between sensor log monitor checks. Accepts seconds (int), `HH:MM:SS`, or ISO8601 durations like `PT10M`. Set to `None` to disable monitoring. | `PT1M` or `0:01:00` or `60` | `0:01:00` |
| SMIB_PLUGIN_SMIBHID_SENSOR_MONITOR_ALERT_THRESHOLD | Time since the last received sensor log after which an alert should be sent. Accepts seconds (int), `HH:MM:SS`, or ISO8601 durations. | `PT1H` or `1:00:00` or `3600` | `1:00:00` |
| SMIB_PLUGIN_SMIBHID_SENSOR_MONITOR_ALERT_RESEND_INTERVAL | Interval to resend alerts while the issue persists. Accepts seconds (int), `HH:MM:SS`, or ISO8601 durations. Set to `None` to only alert once per issue. | `PT10M` or `0:10:00` or `600` | `None` |
| SMIB_PLUGIN_SMIBHID_SENSOR_MONITOR_ALERT_CHANNEL_ID | Slack channel ID where sensor log monitor alerts are posted | `C1234567890` | `code` |
