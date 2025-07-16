import json
import time
from datetime import datetime, timezone

import requests


def main():
    utc_time = datetime.now(timezone.utc)
    utc_timestamp = int(utc_time.timestamp())
    # units = {
    #           "SCD30": {
    #             "co2": "ppm",
    #             "temperature": "C",
    #             "relative_humidity": "%"
    #           },
    #           "BME280": {
    #             "pressure": "hPa",
    #             "temperature": "C",
    #             "humidity": "%"
    #           }
    #         }
    # readings = [
    #     {
    #         "human_timestamp": utc_time.isoformat(),
    #         "data": {
    #             "SCD30": {
    #                 "relative_humidity": 0,
    #                 "temperature": 0,
    #                 "co2": 0
    #             },
    #             "BME280": {
    #                 "pressure": 1019.3,
    #                 "humidity": 48.7,
    #                 "temperature": 20.03
    #             }
    #         },
    #         "timestamp": utc_timestamp
    #     },
    #     {
    #         "timestamp": utc_timestamp,
    #         "data": {
    #             "SCD30": {
    #                 "co2": 1548.1,
    #                 "temperature": 26.3,
    #                 "relative_humidity": 52.9
    #             },
    #             "BME280": {
    #                 "pressure": 632,
    #                 "humidity": 57.64,
    #                 "temperature": 23.05
    #             }
    #         },
    #         "human_timestamp": utc_time.isoformat()
    #     }
    # ]
    #
    # payload = {
    #     "readings": readings,
    #     "units": units
    # }

    payload = {'units': {'SCD30': {'relative_humidity': '%', 'temperature': 'C', 'co2': 'ppm'}, 'BME280': {'pressure': 'hPa', 'temperature': 'C', 'humidity': '%'}}, 'readings': [{'data': {'SCD30': {'temperature': 0.0, 'relative_humidity': 0.0, 'co2': 0.0}, 'BME280': {'pressure': 1017.0, 'humidity': 33.69, 'temperature': 27.52}}, 'human_timestamp': '2025-07-16T19:14:19Z', 'timestamp': 1752693259}, {'timestamp': 1752693248, 'data': {'SCD30': {'co2': 0.0, 'temperature': 0.0, 'relative_humidity': 0.0}, 'BME280': {'pressure': 1017.0, 'humidity': 33.83, 'temperature': 27.49}}, 'human_timestamp': '2025-07-16T19:14:08Z'}, {'human_timestamp': '2021-01-01T00:15:11Z', 'data': {'SCD30': {'relative_humidity': 0.0, 'temperature': 0.0, 'co2': 0.0}, 'BME280': {'pressure': 1017.0, 'humidity': 32.69, 'temperature': 26.84}}, 'timestamp': 1609460111}, {'timestamp': 1609459380, 'data': {'SCD30': {'co2': 0.0, 'temperature': 0.0, 'relative_humidity': 0.0}, 'BME280': {'pressure': 1017.0, 'humidity': 34.42, 'temperature': 26.81}}, 'human_timestamp': '2021-01-01T00:03:00Z'}, {'human_timestamp': '2021-01-01T00:02:32Z', 'data': {'SCD30': {'relative_humidity': 0.0, 'temperature': 0.0, 'co2': 0.0}, 'BME280': {'pressure': 1017.0, 'humidity': 34.77, 'temperature': 26.76}}, 'timestamp': 1609459352}, {'timestamp': 1609459327, 'data': {'SCD30': {'co2': 0.0, 'temperature': 0.0, 'relative_humidity': 0.0}, 'BME280': {'pressure': 1017.0, 'humidity': 33.33, 'temperature': 26.72}}, 'human_timestamp': '2021-01-01T00:02:07Z'}, {'human_timestamp': '2021-01-01T00:01:43Z', 'data': {'SCD30': {'relative_humidity': 0.0, 'temperature': 0.0, 'co2': 0.0}, 'BME280': {'pressure': 1017.0, 'humidity': 33.8, 'temperature': 26.68}}, 'timestamp': 1609459303}, {'timestamp': 1609459274, 'data': {'SCD30': {'co2': 0.0, 'temperature': 0.0, 'relative_humidity': 0.0}, 'BME280': {'pressure': 1017.0, 'humidity': 34.76, 'temperature': 26.67}}, 'human_timestamp': '2021-01-01T00:01:14Z'}, {'human_timestamp': '2021-01-01T00:00:50Z', 'data': {'SCD30': {'relative_humidity': 0.0, 'temperature': 0.0, 'co2': 0.0}, 'BME280': {'pressure': 1017.0, 'humidity': 35.88, 'temperature': 26.61}}, 'timestamp': 1609459250}, {'timestamp': 1609459205, 'data': {'SCD30': {'co2': 0.0, 'temperature': 0.0, 'relative_humidity': 0.0}, 'BME280': {'pressure': 632.0, 'humidity': 57.64, 'temperature': 23.05}}, 'human_timestamp': '2021-01-01T00:00:05Z'}, {'human_timestamp': '2025-07-15T21:30:05Z', 'data': {'SCD30': {'relative_humidity': 0.0, 'temperature': 0.0, 'co2': 0.0}, 'BME280': {'pressure': 1010.1, 'humidity': 42.3, 'temperature': 21.49}}, 'timestamp': 1752615005}]}

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
