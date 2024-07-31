from hammock import Hammock

from .config import HMS_BASE_URL

Hms = Hammock(HMS_BASE_URL, headers={
    "Content-type": "application/json",
    "Accept": "application/json"
})
