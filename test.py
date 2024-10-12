from pprint import pprint
from time import sleep
import requests

node = "40219"
passwd = "790f23b1485a"

while True:
    data = {"port":4567,"data":{"nodes":{"2509":{"node":node,"passwd":passwd,"remote":0}}}}
    r = requests.post('http://localhost:5000/', json=data)
    print(r.status_code)
    pprint(r.json())
    sleep(60*3)
    pprint(r.json())
