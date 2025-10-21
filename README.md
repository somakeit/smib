# SMIB (So Make It Bot)

## Introduction
SMIB is the So Make It Bot, a versatile Slack bot designed for the So Make It maker space. It is built on the [slack-bolt](https://github.com/slackapi/bolt-python) framework with a flexible plugin system, integrated database, HTTP API capabilities, and scheduled task support.

## Features
- **Socket Mode Slack Bot**: Requires no port forwarding or firewall configuration to run on your network
- **Flexible Plugin System** with multiple interfaces:
  - **Slack Integration**: Define your own event listeners to act on Slack events (full [slack-bolt](https://github.com/slackapi/bolt-python) feature set supported)
  - **HTTP API**: Create self-documenting API endpoints using FastAPI (webpages, REST, etc...)
  - **Websockets**: Send and receive real-time updates to connected clients using FastAPI WebSockets
  - **Scheduled Tasks**: Define jobs that run on a schedule using APScheduler
  - **Database Integration**: Store and retrieve data using MongoDB and Beanie ODM
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Extensible Architecture**: Designed to be easily extended with new plugins and features

## Current Plugins
- **Space State** (`space/spacestate`)
  - API Endpoints for setting and retrieving the current space state
  - Websocket endpoint for pushing updates to connected clients
  - Slack integration for posting the current space state to a channel
- **S.M.I.B.H.I.D.** (`space/smibhid`)
  - API Endpoints for receiving data from a [SMIBHID device](https://github.com/somakeit/smibhid)
    - Sensor readings
      - Configurable sensor log monitor to alert when no logs are received within a specified timeframe
    - Button press log
- **How Fresh?** (`space/howfresh`)
  - Slack command `/howfresh`
    - Responds in Slack with the latest sensor readings received from any SMIBHID.
- **Space Welcome** (`space/welcome`)
  - Automatic welcome message for new users when they join the Slack workspace
  - Slack command `/welcome`
    - Sends the welcome message in Slack to the requesting user
  - Read [this](src/plugins/space/welcome/README.md) for information on how the welcome message is built.

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
SMIB uses [traefik](https://github.com/traefik/traefik) as a reverse proxy to route requests to different services:
- MongoDB Express web interface is accessible at `/database/ui`
- SMIB webserver handles all other routes:
    - `/api` - REST API endpoints
    - `/api/docs` - Interactive API documentation (Swagger UI)
    - `/api/redoc` - Alternative API documentation (ReDoc)
    - `/database/docs` - Database schema documentation showing all MongoDB collections and their structure
    - `/ws` - WebSocket connections
    - `/static` - Static files (e.g., images, CSS, JavaScript)
    - `/` - Web pages and application content

The proxy configuration can be customised with these environment variables:
- `SMIB_PROXY_EXTERNAL_PORT`: The external port for the proxy (default: `80`)
- `SMIB_PROXY_TRUSTED_PROXIES`: Trusted IPs for forwarded headers (important if behind another proxy)
- `SMIB_WEBSERVER_PATH_PREFIX`: URL path prefix for all SMIB endpoints (default: `/`)

#### Other Configuration/Documentation
- [Database](https://hub.docker.com/_/mongo)
- [Database Web UI](https://github.com/mongo-express/mongo-express)
- [Proxy](https://doc.traefik.io/traefik/)
- [Socket Proxy](https://github.com/Tecnativa/docker-socket-proxy)

For more detailed S.M.I.B. configuration options, see [SETTINGS.md](SETTINGS.md).

> [!IMPORTANT]
> If you are running MongoDB on an older device or raspberry pi, check what the highest compatible MongoDB version is.
> 
> On a 64-bit Raspberry Pi it's `4.4.18`, so the following environment variable will need to be set: `SMIB_COMPOSE_MONGO_DB_TAG=4.4.18`.
> 
> The easiest way to check is to start up the MongoDB (`smib-db`) container and review the logs.

## Documentation

Once SMIB is running, you can access comprehensive auto-generated documentation at the following endpoints:

### API Documentation
- **`/api/docs`** - Interactive API documentation (Swagger UI)
    - Explore and test all REST API endpoints directly in your browser
    - View request/response schemas and authentication requirements
    - Try out API calls with live data
- **`/api/redoc`** - Alternative API documentation (ReDoc)
    - Clean, readable format optimised for browsing
    - Same OpenAPI specification as Swagger UI with a different layout

### Database Documentation
- **`/database/docs`** - Database schema documentation
    - View all MongoDB collections and their structure
    - See field definitions, data types, and constraints
    - Review indexes configured on each collection
    - Automatically generated from Beanie ODM models

All documentation is automatically updated when new plugins add API endpoints or database models.


## SMIBHID
[SMIBHID](https://github.com/somakeit/smibhid/) is the So Make It Bot Human Interface Device and definitely not a mispronunciation of any insults from a popular 90s documentary detailing the activities of the Jupiter Mining Core.

This device runs on a Raspberry Pi Pico W and provides physical input and output to humans for the SMIB project; Buttons, LEDs, that sort of thing.

Further documentation can be found [in the smibhid repo](https://github.com/somakeit/smibhid/).
### Compatibility
> [!IMPORTANT]
> [SMIBHID v2.1.0](https://github.com/somakeit/smibhid/releases/tag/v2.1.0) is required for compatibility with [SMIB v2.1.0](https://github.com/somakeit/smib/releases/tag/v2.1.0) and later. SMIB v2.1.0 no longer supports the deprecated v1 endpoints, which have been updated in SMIBHID v2.1.0.

## Contributing
Contributions are welcome! Please see the [contributing page](https://github.com/somakeit/smib/contribute) for more information.

## License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
