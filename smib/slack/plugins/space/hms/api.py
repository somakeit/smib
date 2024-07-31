from hammock import Hammock

from .config import HMS_BASE_URL, HMS_CLIENT_ID, HMS_CLIENT_SECRET

Hms = Hammock(HMS_BASE_URL, headers={
    "Content-type": "application/json",
    "Accept": "application/json"
})

if __name__ == '__main__':
    endpoint = Hms.api.oauth.token
    print(endpoint)
    result = endpoint.POST(data={
        "grant_type": "client_credentials",
        "client_id": HMS_CLIENT_ID,
        "client_secret": HMS_CLIENT_SECRET
    })

    print(result)
    print(result.json())
