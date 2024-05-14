## Docker deployment
### Installation
- Clone the repository to your target server host
- Install docker if not already present
- Set the slack tokens as environment variables using either method below:
  - Linux
    - `export SLACK_APP_TOKEN=<app-token>`
    - `export SLACK_BOT_TOKEN=<bot-token>`
  - .env File
    - Create a file called `.env` alongside the docker-compose.yml file (see `template.env` in the repo)
- Issue one of the following commands:
  - Local Build: `docker compose up -d --build`
  - Develop Branch Build: `docker compose -f docker-compose-develop.yml up -d --build`
  - Master Branch Build: `docker compose -f docker-compose-master.yml up -d --build`


### Configuration
The host ports mapped for the slack server and webserver should be configured in the docker compose file, however it is also possible to override the ports in the server configs directly if you are not using docker.

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


