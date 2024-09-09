from pprint import pprint
import requests

data = {"port":4567,"data":{"nodes":{"2509":{"node":"2509","passwd":"435009","remote":0}}}}
r = requests.post('http://localhost:5000/', json=data)
print(r.status_code)
pprint(r.json())