import json
import time
from datetime import datetime, timezone

import requests


def main():
    utc_time = datetime.now(timezone.utc)
    utc_timestamp = int(utc_time.timestamp())
    data = [
        {"event": {"button_name": "Space Open", "button_id": "space_open"}, "type": "button_press",
         "timestamp": utc_timestamp},
        {"event": {"button_name": "Space Closed", "button_id": "space_closed"}, "type": "button_press",
         "timestamp": utc_timestamp},
        {"event": {"button_name": "Space Open", "button_id": "space_open"}, "type": "button_press",
         "timestamp": utc_timestamp},
        {"event": {"button_name": "Space Closed", "button_id": "space_closed"}, "type": "button_press",
         "timestamp": utc_timestamp}
    ]
    headers = {"Content-Type": "application/json", 'device-hostname': "smibhid-dummy"}
    url = f"http://localhost/smib/event/smibhid_ui_log"
    print(f"url: {url}")
    print(f"headers: {headers}")
    print(f"data: {data}")
    print(f"JSON data: {json.dumps(data)}")
    response = requests.post(url, headers=headers, data=json.dumps(data), verify=False)

    print(response.status_code)


if __name__ == '__main__':
    main()
