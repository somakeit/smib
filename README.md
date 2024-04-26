## Docker deployment
### Installation
- Clone the repository to your target server host
- Install docker if not already present
- Set the slack tokens as environment variables as follows:
  - Linux
    - `export SLACK_APP_TOKEN=<app-token>`
    - `export SLACK_BOT_TOKEN=<bot-token>`
  - .env File
    - Create a file called `.env` alongside the docker-compose.yml file (see `template.env` in the repo)
- Issue command `docker compose up -d --build`

### Configuration
The host ports mapped for the slack server and webserver should be configured in the docker compose file, however it is also possible to override the ports in the server configs directly if you are not using docker.
