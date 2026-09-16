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

### Space Relay State Plugin

| Environment Variable                                                               | Description                                                                                                                                                                                              | Example                        | Default                                                                                                           |
|------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------|-------------------------------------------------------------------------------------------------------------------|
| SMIB_PLUGIN_SPACE_RELAY_STATE_MONITOR_INTERVAL | Interval between periodic sweeps of all known relay states, re-checking drift and relay-lifetime thresholds independent of new incoming reports (catches e.g. a relay stuck ON with no new events landing). Accepts seconds (int), `HH:MM:SS`, or ISO8601 durations like `PT5M`. Set to `None` to disable. | `PT5M` or `0:05:00` or `300` | `0:05:00` |
| SMIB_PLUGIN_SPACE_RELAY_STATE_TOTAL_ACTIVE_SECONDS_DRIFT_WARNING_THRESHOLD_SECONDS | Log a warning when SMIB's computed cumulative relay on-time (since the last reset) and S.M.I.B.H.I.D.'s reported total diverge by more than this many seconds                                            | `600`                          | `300`                                                                                                             |
| SMIB_PLUGIN_SPACE_RELAY_STATE_RELAY_LIFETIME_WARNING_THRESHOLD                     | On-time since the last reset after which a relay-lifetime Slack alert is sent. Accepts seconds (int), `HH:MM:SS`, or ISO8601 durations. Set to `None` to disable the alert.                              | `P30D` or `720:00:00`          | `None`                                                                                                            |
| SMIB_PLUGIN_SPACE_RELAY_STATE_RELAY_LIFETIME_ALERT_CHANNEL_ID                      | Slack channel ID where relay-lifetime alerts are posted                                                                                                                                                  | `C1234567890`                  | `code`                                                                                                            |
| SMIB_PLUGIN_SPACE_RELAY_STATE_RELAY_LIFETIME_ALERT_RESEND_INTERVAL                 | Interval to resend the relay-lifetime Slack alert while on-time since reset remains over threshold. Accepts seconds (int), `HH:MM:SS`, or ISO8601 durations. Set to `None` to only alert once per cycle. | `P7D` or `168:00:00`           | `None`                                                                                                            |
| SMIB_PLUGIN_SPACE_RELAY_STATE_RELAY_NAME                                           | Friendly name for the tracked relay/filter, used in the alert message                                                                                                                                    | `Extractor Fan Filter`         | `Relay`                                                                                                           |
| SMIB_PLUGIN_SPACE_RELAY_STATE_RELAY_LIFETIME_ALERT_MESSAGE_TEMPLATE                | Slack alert message template. Supports `{device}`, `{relay_name}`, `{duration}`, `{threshold}` placeholders                                                                                              | `{relay_name} needs replacing` | `:warning: {relay_name} on {device} has been active for {duration} since the last reset, exceeding the {threshold} threshold — {relay_name} may need replacing.` |
| SMIB_PLUGIN_SPACE_RELAY_STATE_DRIFT_WARNING_ALERT_CHANNEL_ID                       | Slack channel ID where relay state drift warnings are posted (independent of the relay-lifetime alert channel)                                                                                           | `C1234567890`                  | `code`                                                                                                            |
| SMIB_PLUGIN_SPACE_RELAY_STATE_DRIFT_WARNING_ALERT_RESEND_INTERVAL                  | Interval to resend the drift warning Slack alert while drift remains over threshold. Accepts seconds (int), `HH:MM:SS`, or ISO8601 durations. Set to `None` to only alert once per drift episode.        | `PT1H` or `1:00:00`            | `None`                                                                                                            |

### Space State Plugin

| Environment Variable | Description | Example | Default |
|---------------------|-------------|---------|---------|
| SMIB_PLUGIN_SPACE_STATE_SPACE_OPEN_ANNOUNCE_CHANNEL_ID | Slack channel ID where space open/close announcements are posted | `C1234567890` | `space-open-announce` |

### Static Files Plugin

| Environment Variable | Description | Example | Default |
|---------------------|-------------|---------|---------|
| SMIB_PLUGIN_STATIC_FILES_STATIC_FILES_DIRECTORY | Directory path where static files are stored and served from | `public/assets` | `static` |

### S.M.I.B.H.I.D. Plugin
| Environment Variable | Description | Example | Default |
|---------------------|-------------|---------|---------|
| SMIB_PLUGIN_SMIBHID_SENSOR_MONITOR_INTERVAL | Interval between sensor log monitor checks. Accepts seconds (int), `HH:MM:SS`, or ISO8601 durations like `PT10M`. Set to `None` to disable monitoring. | `PT1M` or `0:01:00` or `60` | `0:01:00` |
| SMIB_PLUGIN_SMIBHID_SENSOR_MONITOR_ALERT_THRESHOLD | Time since the last received sensor log after which an alert should be sent. Accepts seconds (int), `HH:MM:SS`, or ISO8601 durations. | `PT1H` or `1:00:00` or `3600` | `1:00:00` |
| SMIB_PLUGIN_SMIBHID_SENSOR_MONITOR_ALERT_RESEND_INTERVAL | Interval to resend alerts while the issue persists. Accepts seconds (int), `HH:MM:SS`, or ISO8601 durations. Set to `None` to only alert once per issue. | `PT10M` or `0:10:00` or `600` | `None` |
| SMIB_PLUGIN_SMIBHID_SENSOR_MONITOR_ALERT_CHANNEL_ID | Slack channel ID where sensor log monitor alerts are posted | `C1234567890` | `code` |
