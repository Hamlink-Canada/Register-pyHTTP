"""Simple looped test client that POSTs registration JSON to the local app.

Useful for quickly exercising the registration endpoint during development.
Adjust `node` and `passwd` values to match entries in your test DB.
"""

from pprint import pprint
from time import sleep
import requests

node = "40219"
passwd = "790f23b1485a"

while True:
    # Build the minimal registration payload expected by the API
    data = {"port": 4567, "data": {"nodes": {"2509": {"node": node, "passwd": passwd, "remote": 0}}}}
    r = requests.post('http://localhost:5000/', json=data)
    print(r.status_code)
    pprint(r.json())
    # Wait 3 minutes between registrations to simulate a refresh
    sleep(60 * 3)
    pprint(r.json())
