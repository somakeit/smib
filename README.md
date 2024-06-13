## Python Version
Python 3.12.3

## Docker deployment
### Installation
- Clone the repository to your target server host
- Install docker if not already present
- Set the environment variables (minimum of the slack tokens) using either method below. See [template.env](template.env) for all possible environment variables.
  - `docker-compose` File - **Highest Precedence**
    - Set the variables in your docker-compose file
  - `.env` File
    - Create a file called `.env` alongside the docker-compose.yml file (see `template.env` in the repo)
- Issue one of the following commands:
  - Local Build: `docker compose up -d --build`
  - Develop Branch Build: `docker compose -f docker-compose-develop.yml up -d --build`
  - Master Branch Build: `docker compose -f docker-compose-master.yml up -d --build`


### Configuration

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

## SMIBHID
[SMIBHID](smibhid/README.md) is the So Make It Bot Human Interface Device and definitely not a mispronunciation of any insults from a popular 90s documentary detailing the activites of the Jupiter Mining Core.

This device run on a Raspberry Pi Pico W and provides physical input and output to humans for the SMIB project; Buttons, LEDs, that sort of thing.

Further documentation can be found [in the smibhid folder](smibhid/).

## Legacy SMIB Commands
Currently, the old [SMIB Commands](https://github.com/somakeit/smib-commands) do not work with the new SMIB.

The old [SMIB](https://github.com/somakeit/smib) worked using the Slack RTM api. This API has been replaced with the Events API. 

Previously, SMIB Commands were created as the only way to interact with SMIB.

I think some form of backwards compatibility or similar functionality would be good. Work on a `ShellPluginLoader` was started but parked as it was not the main focus of the new amped up SMIB [MVP](https://en.wikipedia.org/wiki/Minimum_viable_product)

An [issue](https://github.com/somakeit/S.M.I.B./issues/83) has been created to track the progress and gather ideas.

## Version
When bumping the poetry version (in pyproject.toml), the `HID` class (part of SMIBHID) `version` attribute also needs manually updating.

> [!IMPORTANT]
> This version needs to match the release when it goes into the `master` branch. 
