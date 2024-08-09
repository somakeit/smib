import json
import time

import requests


def main():
    data = [
        {"event": {"button_name": "Space Open", "button_id": "space_open"}, "type": "button_press",
         "timestamp": int(time.time())},
        {"event": {"button_name": "Space Closed", "button_id": "space_closed"}, "type": "button_press",
         "timestamp": int(time.time())},
        {"event": {"button_name": "Space Open", "button_id": "space_open"}, "type": "button_press",
         "timestamp": int(time.time())},
        {"event": {"button_name": "Space Closed", "button_id": "space_closed"}, "type": "button_press",
         "timestamp": int(time.time())}
    ]
    headers = {'device-hostname': "smibhid-dummy"}
    url = f"http://localhost/smib/event/smibhid_ui_log"
    print(url)
    response = requests.post(url, headers=headers, data=json.dumps(data), verify=False)

    print(response.status_code)


if __name__ == '__main__':
    main()
