import json
import time
from datetime import datetime, timezone

import requests


def main():
    utc_time = datetime.now(timezone.utc)
    utc_timestamp = int(utc_time.timestamp())
    units = {
              "SCD30": {
                "co2": "ppm",
                "temperature": "C",
                "relative_humidity": "%"
              },
              "BME280": {
                "pressure": "hPa",
                "temperature": "C",
                "humidity": "%"
              }
            }
    readings = [
        {
            "human_timestamp": utc_time.isoformat(),
            "data": {
                "SCD30": {
                    "relative_humidity": 0,
                    "temperature": 0,
                    "co2": 0
                },
                "BME280": {
                    "pressure": 1019.3,
                    "humidity": 48.7,
                    "temperature": 20.03
                }
            },
            "timestamp": utc_timestamp
        },
        {
            "timestamp": utc_timestamp,
            "data": {
                "SCD30": {
                    "co2": 1548.1,
                    "temperature": 26.3,
                    "relative_humidity": 52.9
                },
                "BME280": {
                    "pressure": 632,
                    "humidity": 57.64,
                    "temperature": 23.05
                }
            },
            "human_timestamp": utc_time.isoformat()
        }
    ]

    payload = {
        "readings": readings,
        "units": units
    }

    headers = {"Content-Type": "application/json", 'device-hostname': "smibhid-dummy"}
    url = f"http://localhost/smib/event/smibhid_sensor_log"
    print(f"url: {url}")
    print(f"headers: {headers}")
    print(f"data: {payload}")
    print(f"JSON data: {json.dumps(payload)}")
    response = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)

    print(response.status_code)


if __name__ == '__main__':
    main()
