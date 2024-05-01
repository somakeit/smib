## Docker deployment
### Installation
- Clone the repository to your target server host
- Install docker if not already present
- Issue command ```docker compose up -d --build```

### Configuration
The host ports mapped for the slack server and webserver should be configured in the docker compose file, however it is also possible to override the ports in the server configs directly if you are not using docker.

## SMIBHID
[SMIBHID](smibhid/README.md) is the So Make It Bot Human Interface Device and definitely not a mispronunciation of any insults from a popular 90s documentary detailing the activites of the Jupiter Mining Core.

This device run on a Raspberry Pi Pico W and provides physical input and output to humans for the SMIB project; Buttons, LEDs, that sort of thing.

Further documentation can be found [in the smibhid folder](smibhid/).