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

For a comprehensive list of all configuration settings, see [SETTINGS.md](SETTINGS.md).

### Slack App Creation
- If you don't already have a Slack Workspace, [create one](https://slack.com/get-started?entry_point=help_center#/createnew).
- Follow the [Creating apps using manifests](https://api.slack.com/reference/manifests#creating_apps) instructions to create a Slack App from the included [manifest](slack-manifest.yaml) and install it into your workspace.
- Once created, go to your [installed apps list](https://api.slack.com/apps) and select the newly installed app.
  - Find the `App-Level Tokens` section of the page and click `Generate Token and Scopes`.
    - Create a token with the `connections:write` scope. This allows SMIB to establish a Websocket connection to Slack.
    - Make sure to copy this token, as this will be used as your `SMIB_SLACK_APP_TOKEN` environment variable. This should start with `xapp-`
  - On the side navigation panel, click the `OAuth and Permissions` button.
    - You should find a pre-generated `Bot User OAuth Token` under the `OAuth Tokens` section of this page.
    - Make sure to copy this token, as this will be used as your `SMIB_SLACK_BOT_TOKEN` environment variable. This should start with `xoxb-`

### Running with Docker
The easiest way to run SMIB is with Docker Compose:

- Clone the repository to your target server host
- Install docker if not already present
  - If installing on a Raspberry Pi (recommend a pi4), ensure you use a 64 bit OS and follow the [Debian install instructions from Docker](https://docs.docker.com/engine/install/debian/).
- Set the environment variables (minimum of the slack tokens). See [template.env](template.env) for all possible environment variables.
  - `.env` File
    - Create a file called `.env` alongside the docker-compose.yml file (see `template.env` in the repo)
- To build a specific version/tag:
  - Use git to checkout the specific branch/tag; e.g. `git checkout v2.0.0`
- Issue the following command to build and run the local copy of the code: `docker compose up -d --build`

#### Proxy Configuration
SMIB includes a built-in Traefik reverse proxy that handles routing to the various services:
- API endpoints (default: `/api`)
- Static files (at `/static`)
- MongoDB Express UI (at `/database/ui`)

The proxy configuration can be customised with these environment variables:
- `SMIB_PROXY_EXTERNAL_PORT`: The external port for the proxy (default: `80`)
- `SMIB_PROXY_TRUSTED_PROXIES`: Trusted IPs for forwarded headers (important if behind another proxy)
- `SMIB_WEBSERVER_PATH_PREFIX`: URL path prefix for all API endpoints (default: `/api`)

#### Other Configuration/Documentation
- [Database](https://hub.docker.com/_/mongo)
- [Database Web UI](https://github.com/mongo-express/mongo-express)
- [Proxy](https://doc.traefik.io/traefik/)
- [Socket Proxy](https://github.com/Tecnativa/docker-socket-proxy)

For more detailed S.M.I.B. configuration options, see [SETTINGS.md](SETTINGS.md).

> [!IMPORTANT]
> If you are running MongoDB on an older device or raspberry pi, check what the highest compatible MongoDB version is.
> 
> On a 64-bit Raspberry Pi it's 4.4.18`, so the following environment variable will need to be set: `SMIB_COMPOSE_MONGO_DB_TAG=4.4.18`.
> 
The easiest way to check is to start up the MongoDB (`smib-db`) container and review the logs.

## SMIBHID
[SMIBHID](https://github.com/somakeit/smibhid/) is the So Make It Bot Human Interface Device and definitely not a mispronunciation of any insults from a popular 90s documentary detailing the activities of the Jupiter Mining Core.

This device runs on a Raspberry Pi Pico W and provides physical input and output to humans for the SMIB project; Buttons, LEDs, that sort of thing.

Further documentation can be found [in the smibhid repo](https://github.com/somakeit/smibhid/).

## Contributing
Contributions are welcome! Please see the [contributing page](https://github.com/somakeit/smib/contribute) for more information.

## License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
