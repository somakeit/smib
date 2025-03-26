# SMIB (So Make It Bot)
## Introduction
SMIB is the So Make It Bot. The architecture is a set of docker containers configured to work together, that can run on a pi4 or similar and provide slack bot interactivity with a maker space (or any space).

### Features
- A socket mode slack bot server that requires no port forwarding or firewall config to get going on your network.
- Web server with plugin architecture providing a REST API with swagger API documentation, so you can write your own plugins that can be called by REST API and executed by the slack bot - allows creating web pages or local devices (such as SMIBHID) that drive the slack bot without the need for leaving the local network.
- Stateful database storage for storing information like space state for coordination among multiple bots/endpoints.
- SMIBHID (SMIB Human Interface Device) - A Pi Pico based interface device that provides buttons, displays and any other human interface to the slack bot via the REST API. See the [SMIBHID docs](smibhid/README.md) for more information.

## Slack App Creation
- If you don't already have a Slack Workspace, [create one](https://slack.com/get-started?entry_point=help_center#/createnew).
- Follow the [Creating apps using manifests](https://api.slack.com/reference/manifests#creating_apps) instructions to create a Slack App from the included [manifest](manifest.yaml) and install it into your workspace.
- Once created, go to your [installed apps list](https://api.slack.com/apps) and select the newly installed app.
  - Find the `App-Level Tokens` section of the page and click `Generate Token and Scopes`.
    - Create a token with the `connections:write` scope. This allows SMIB to establish a Websocket connection to Slack.
    - Make sure to copy this token, as this will be used as your `SLACK_APP_TOKEN` envurironment variable. This should start with `xapp-`
  - On the side navigation panel, click the `OAuth and Permissions` button.
    - You should find a pre-generated `Bot User OAuth Token` under the `OAuth Tokens` section of this page.
    - Make sure to copy this token, as this will be used as your `SLACK_BOT_TOKEN` envurironment variable. This should start with `xapp-`

## Docker deployment
### Supported Python Version
Python 3.12.3

### Installation
- Clone the repository to your target server host
- Install docker if not already present
  - If installing on a Raspberry Pi (recommend a pi4), ensure you use a 64 bit OS and follow the [Debian install instructions from Docker](https://docs.docker.com/engine/install/debian/).
- Set the environment variables (minimum of the slack tokens) using either method below. See [template.env](template.env) for all possible environment variables.
  - `docker-compose` File - **Highest Precedence**
    - Set the variables in your docker-compose file
  - `.env` File
    - Create a file called `.env` alongside the docker-compose.yml file (see `template.env` in the repo)
- Issue one of the following commands:
  - Local Build: `docker compose up -d --build`
  - Branch Build (default master): `docker compose -f docker-compose-branch.yml up -d --build`
    - To specify the branch, do one of the following:
      - Prefix the command with `SMIB_BRANCH=<branch>`
        - e.g `SMIB_BRANCH=master docker compose -f docker-compose-branch.yml up -d --build`
      - Set environment variable in a `.env` file thats alongside the `docker-compose-branch.yml` file


### SMIB Slack/Webserver Configuration

#### Network Ports
The host ports mapped for the slack server and webserver should be configured in the docker compose file, however it is also possible to override the ports in the server configs directly if you are not using docker.

#### External Config Files
Current files:
- `logging.json` (located at [smib/logging.json](smib/logging.json) in the repo)
- `.env`

This is mapped to `/app/config` in the container

> [!IMPORTANT]
> If you map `/app/config` to a host directory, then you *MUST* add the 2 external files to this location.

You can make this location accessible by Mapping the internal directory to a volume or bind mount in the docker compose file.

Linux:
```yaml
volumes:
  - /etc/smib/:/app/config/
```

Windows:
```yaml
volumes:
  - C:/smib/config:/app/config/
```

Local Development:
- Set the `_EXTERNAL_CONFIG_LOCATION` environment variable to the directory containing the External Config Files

#### Logging
Map the internal /app/logs directory to a volume or bind mount in the docker compose to store the logs outside the containers

Linux:
```yaml
volumes:
  - /var/log/smib/slack/:/app/logs/
```

Windows:
```yaml
volumes:
  - C:/smib/slack/logs:/app/logs/
```

### Database and Database Web UI Configuration
To set environment varaibles for the `smib-db` and `smib-db-ui` containers, you must do one of the following:
  - `docker-compose` File - **Highest Precedence**
    - Set the variables in your docker-compose file
  - `.env` File
    - Create a file called `.env` alongside the docker-compose.yml file. See links below for possible values
      - [Database Web UI Configuration](https://github.com/mongo-express/mongo-express)
      - [Database Configuration](https://hub.docker.com/_/mongo)

## SMIBHID
[SMIBHID](smibhid/README.md) is the So Make It Bot Human Interface Device and definitely not a mispronunciation of any insults from a popular 90s documentary detailing the activites of the Jupiter Mining Core.

This device runs on a Raspberry Pi Pico W and provides physical input and output to humans for the SMIB project; Buttons, LEDs, that sort of thing.

Further documentation can be found [in the smibhid folder](smibhid/).

## Legacy SMIB Commands
Currently, the old [SMIB Commands](https://github.com/somakeit/smib-commands) do not work with the new SMIB.

The old [SMIB](https://github.com/somakeit/smib-old) worked using the Slack RTM API. This API has been replaced with the Events API. 

Previously, SMIB Commands were created as the only way to interact with SMIB.

I think some form of backwards compatibility or similar functionality would be good. Work on a `ShellPluginLoader` was started but parked as it was not the main focus of the new amped up SMIB [MVP](https://en.wikipedia.org/wiki/Minimum_viable_product)

An [issue](https://github.com/somakeit/smib/issues/83) has been created to track the progress and gather ideas.

## Version
When bumping the poetry version (in pyproject.toml), the `HID` class (part of SMIBHID) `version` attribute also needs manually updating.

> [!IMPORTANT]
> This version needs to match the release when it goes into the `master` branch. 
