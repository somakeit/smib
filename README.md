## Docker deployment
### Installation
- Clone the repository to your target server host
- Install docker if not already present
- Set the slack tokens and DB Web UI Credentials as environment variables using either method below:
  - Linux
    - `export SLACK_APP_TOKEN=<app-token>`
    - `export SLACK_BOT_TOKEN=<bot-token>`
    - `export ME_CONFIG_BASICAUTH_USERNAME=<mongo-express-basicauth-username>`
    - `export ME_CONFIG_BASICAUTH_PASSWORD=<mongo-express-basicauth-password>`
  - .env File
    - Create a file called `.env` alongside the docker-compose.yml file (see `template.env` in the repo)
- Issue one of the following commands:
  - Local Build: `docker compose up -d --build`
  - Develop Branch Build: `docker compose -f docker-compose-develop.yml up -d --build`
  - Master Branch Build: `docker compose -f docker-compose-master.yml up -d --build`


### Configuration
The host ports mapped for the slack server and webserver should be configured in the docker compose file, however it is also possible to override the ports in the server configs directly if you are not using docker.

#### External Config Files
Currently, the only external config file is the logging.json file.

This is mapped to /app/config in the container

You can make this location accessible by Mapping the internal directiry to a volume or bind mount in the docker compose file.

Linux:
```yaml
volumes:
  - /var/smib/config:/app/config/
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
  - /var/smib/slack/logs:/app/logs/
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


