#!/usr/bin/env python3
import os
import sys
import urllib.request

port = os.environ.get("SMIB_WEBSERVER_PORT", "80")
url = f"http://localhost:{port}/api/ping"
req = urllib.request.Request(url, headers={"x-skip-logging": "true"})

try:
    with urllib.request.urlopen(req, timeout=5) as r:
        sys.exit(0 if r.status == 200 else 1)
except Exception:
    sys.exit(1)
