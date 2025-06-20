# SMIB (So Make It Bot)

## Introduction
SMIB is the So Make It Bot, a versatile Slack bot designed for the So Make It maker space. It is built on the [slack-bolt](https://github.com/slackapi/bolt-python) framework with a flexible plugin system, integrated database, HTTP API capabilities, and scheduled task support.

## Features
- **Socket Mode Slack Bot**: Requires no port forwarding or firewall configuration to run on your network
- **Flexible Plugin System** with multiple interfaces:
  - **Slack Integration**: Define your own event listeners to act on Slack events (full [slack-bolt](https://github.com/slackapi/bolt-python) feature set supported)
  - **HTTP API**: Create self-documenting API endpoints using FastAPI (webpages, REST, etc...)
  - **Scheduled Tasks**: Define jobs that run on a schedule using APScheduler
  - **Database Integration**: Store and retrieve data using MongoDB and Beanie ODM
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Extensible Architecture**: Designed to be easily extended with new plugins and features

## Setup and Configuration

### Slack App Creation
- If you don't already have a Slack Workspace, [create one](https://slack.com/get-started?entry_point=help_center#/createnew).
- Follow the [Creating apps using manifests](https://api.slack.com/reference/manifests#creating_apps) instructions to create a Slack App from the included [manifest](slack-manifest.yaml) and install it into your workspace.
- Once created, go to your [installed apps list](https://api.slack.com/apps) and select the newly installed app.
  - Find the `App-Level Tokens` section of the page and click `Generate Token and Scopes`.
    - Create a token with the `connections:write` scope. This allows SMIB to establish a Websocket connection to Slack.
    - Make sure to copy this token, as this will be used as your `SLACK_APP_TOKEN` environment variable. This should start with `xapp-`
  - On the side navigation panel, click the `OAuth and Permissions` button.
    - You should find a pre-generated `Bot User OAuth Token` under the `OAuth Tokens` section of this page.
    - Make sure to copy this token, as this will be used as your `SLACK_BOT_TOKEN` environment variable. This should start with `xapp-`

### Running with Docker
The easiest way to run SMIB is with Docker Compose:

- Clone the repository to your target server host
- Install docker if not already present
  - If installing on a Raspberry Pi (recommend a pi4), ensure you use a 64 bit OS and follow the [Debian install instructions from Docker](https://docs.docker.com/engine/install/debian/).
- Set the environment variables (minimum of the slack tokens). See [template.env](template.env) for all possible environment variables.
  - `.env` File
    - Create a file called `.env` alongside the docker-compose.yml file (see `template.env` in the repo)
- Issue the following command to build and run the local copy of the code: `docker compose up -d --build`
- To build a specific version/tag:
  - Set the `SMIB_BUILD_GIT_TAG` environment variable in the `.env` file to the branch/tag name.
    - e.g. `SMIB_BUILD_GIT_TAG=v2.0.0` or `SMIB_BUILD_GIT_TAG=master`
  - `docker compose up -d --build`

### Environment Variables
Here are all the SMIB environment variables, along with some other ones that are used in the docker-compose files to make the stack work.

| Variable | Description | Example                    | Default | Where Used |
|----------|-------------|----------------------------|---------|------------|
| **Slack Configuration** ||                            |||
| `SLACK_BOT_TOKEN` | Slack Bot User OAuth Token | `xoxb-1234567890-...`      | *Required* | SMIB |
| `SLACK_APP_TOKEN` | Slack App-Level Token | `xapp-1-A1234...`          | *Required* | SMIB |
| `SLACK_SIGNING_SECRET` | Slack Signing Secret for Request Verification | `a123b456c789...`          | Auto-generated | SMIB |
| **Webserver Configuration** ||                            |||
| `WEBSERVER_HOST` | Host address for the web server | `0.0.0.0`                  | `127.0.0.1` | SMIB |
| `WEBSERVER_PORT` | Port for the web server | `8000`                     | `80` | SMIB |
| `WEBSERVER_PATH_PREFIX` | URL path prefix for all endpoints | `/api/v1`                  | `/` | SMIB |
| `WEBSERVER_FORWARDED_ALLOW_IPS` | IPs allowed for proxy forwarding | `*` or `1.2.3.4,5.6.7.8`   | `*` | SMIB |
| **MongoDB Configuration** ||                            |||
| `MONGO_DB_HOST` | MongoDB server hostname | `mongodb.example.com`      | `localhost` | SMIB |
| `MONGO_DB_PORT` | MongoDB server port | `27017`                    | `27017` | SMIB |
| `MONGO_DB_NAME` | MongoDB database name | `smib_prod`                | `smib` | SMIB |
| **Logging** ||                            |||
| `ROOT_LOG_LEVEL` | Root logger level | `DEBUG`                    | `INFO` | SMIB |
| **Docker Build Configuration** ||                            |||
| `SMIB_BUILD_GIT_TAG` | Git tag/branch to build from | `master` or `v1.0.0`       | `.` | Docker Compose |
| **Docker Service Configuration** ||                            |||
| `SMIB_WEBSERVER_EXTERNAL_PORT` | External port mapping for the web server | `8080`                     | `80` | Docker Compose |
| `SMIB_WEBSERVER_INTERNAL_PORT` | Internal container port for the web server | `8000`                     | `80` | Docker Compose |
| **MongoDB Docker Configuration** ||                            |||
| `MONGO_DB_TAG` | MongoDB Docker image tag | `6.0`                      | `latest` | Docker Compose |
| **MongoDB Express UI Configuration** ||                            |||
| `MONGO_DB_UI_PORT` | Port for MongoDB Express web interface | `8081`                     | `8081` | Docker Compose |
| `ME_CONFIG_MONGODB_URL` | MongoDB connection URL for Express UI | `mongodb://smib-db:27017/` | `mongodb://smib-db:27017/` | Docker Compose |

## SMIBHID
[SMIBHID](https://github.com/somakeit/smibhid/) is the So Make It Bot Human Interface Device and definitely not a mispronunciation of any insults from a popular 90s documentary detailing the activites of the Jupiter Mining Core.

This device runs on a Raspberry Pi Pico W and provides physical input and output to humans for the SMIB project; Buttons, LEDs, that sort of thing.

Further documentation can be found [in the smibhid repo](https://github.com/somakeit/smibhid/).

## Contributing
Contributions are welcome! Please see the [contributing page](https://github.com/somakeit/smib/contribute) for more information.

## License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.