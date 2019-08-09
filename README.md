# lntenna-python

A library and REST API interface to use gotenna, txtenna and lntenna functionality

### In a terminal:
create a python 2.7 venv and activate it,

`pip install -r requirements.txt`

`lntenna/api/python server.py`

or to run in gateway (online connection) mode:

`lntenna/api/python server.py --gateway`

## API tests
In a python console:

```
import requests, time
from pprint import pprint

url = "http://127.0.0.1:5000"
s = requests.Session()
```

#### SDK test
```
sdk_params = {
    "sdk_token": "H18BVEYPTAAEVAFEXgIOFUECAgNHUlgDB0APAgFREB0BWRcIAkdRQAAHXgUOUAxc"
}
sdk_test = s.post(url=url + "/gotenna/api/v1.0/sdk_token", json=sdk_params)
pprint(sdk_test.json())
```
#### reset connection vars test
`reset_test = s.get(url=url + '/gotenna/api/v1.0/reset')`

*still sometimes requires restarting the server to make a new connection

#### set gid
```
gid_params = {"gid": 87654321}
gid_test = s.post(url=url + "/gotenna/api/v1.0/set_gid", json=gid_params)
pprint(gid_test.json())
```

#### set geo region
```
geo_params = {"region": 2}
geo_test = s.post(url=url + "/gotenna/api/v1.0/set_geo_region", json=geo_params)
pprint(geo_test.json())
```

#### send_broadcast
```
msg_params = {"message": "Hello, world!"}
broadcast_test = s.post(url=url + "/gotenna/api/v1.0/send_broadcast", json=msg_params)
pprint(broadcast_test.json())
```

#### get_device_type
```
device_type = s.get(url=url + "/gotenna/api/v1.0/get_device_type")
pprint(device_type.json())
```

#### list geo_regions
```
avail_regions = s.get(url=url + "/gotenna/api/v1.0/list_geo_region")
pprint(avail_regions.json())
```

#### get can_connect
```
can_connect = s.get(url=url + "/gotenna/api/v1.0/can_connect")
pprint(can_connect.json())
```

#### retrieve stored connection events
```
connection_events = s.get(url=url + "/gotenna/api/v1.0/get_connection_events")
pprint(connection_events.json())
```

#### get_system_info
```
system_info = s.get(url=url + "/gotenna/api/v1.0/get_system_info")
pprint(system_info.json())
```

#### retrieve all messages received by the device
```
message_events = s.get(url=url + "/gotenna/api/v1.0/get_messages")
pprint(message_events.json())
```

#### test api_request
```
get_test = {"url": "https://api.blockstream.space/testnet/info"}
get_api_call = s.get(url=url + "/gotenna/api/v1.0/api_request", json=get_test)

post_data = {"message": "test_msg", "bid": 10000}
post_test = {"url": "https://api.blockstream.space/testnet/order", "data": post_data}
post_api_call = s.post(url=url + "/gotenna/api/v1.0/api_request", json=post_test)
```

# txtenna tests

#### configure bitcoin params
```
btc_config = {
    "btc_conf_file": "/Users/will/Library/Application Support/Bitcoin/testnet3/bitcoin.conf",
    "btc_network": "testnet",
}
configure_bitcoin = s.post(url=url + "/bitcoin/api/v1.0/configure", json=btc_config)
```

#### getrawtransaction
```
getrawtx = {"tx_id": "633de641ac179890b69c103fba76387ecaecd431a18e763a0d4764dbc1193031"}
raw_tx_test = s.get(url=url + "/bitcoin/api/v1.0/rpc_getrawtransaction", json=getrawtx)
```

#### bitcoind-rpc_rawproxy (using getbalance and getrawtransaction)
```
raw_tx_data = raw_tx_test.json()

raw_proxy_json = {"command": "getbalance", "args": None}
raw_proxy_test = s.post(url=url + "/bitcoin/api/v1.0/rpc_rawproxy", json=raw_proxy_json)
print(raw_proxy_test.json())

raw_proxy_json2 = {
    "command": "getrawtransaction",
    "args": "633de641ac179890b69c103fba76387ecaecd431a18e763a0d4764dbc1193031, True",
}
raw_proxy_test2 = s.post(
    url=url + "/bitcoin/api/v1.0/rpc_rawproxy", json=raw_proxy_json2
)
print(raw_proxy_test2.json())
```

#### GetAPI call
Make sure server is running with --gateway flag. See lntenna/api/server.py L60
```
api_req = {"type": "GET",
           "url": "https://api.blockstream.space/testnet/info"}
full_req = {"api_request": api_req}
api_test = s.post(url=url + "/gotenna/api/v1.0/api_request", json=full_req)
```

# manual equivalents
```
from lntenna.gotenna_core import connection
from goTenna.settings import GID

c = connection.Connection()
c.sdk_token(
    sdk_token="H18BVEYPTAAEVAFEXgIOFUECAgNHUlgDB0APAgFREB0BWRcIAkdRQAAHXgUOUAxc"
)
c.set_gid(gid=12345678)
c.set_geo_region(region=2)
# power on goTenna
c.send_broadcast("Hello, world!")
sender_gid = GID(gid_val=87654321, gid_type=GID.PRIVATE)
c.send_private(sender_gid, "Hello, world2!")
c.get_device_type()
c.list_geo_region()
c.can_connect()
e = c.events.get_all_connection()
i = c.get_system_info()
msgs = c.events.get_all_messages()
```
#### txtenna
```
c.btc_conf_file = (
    "/Users/will/Library/Application Support/Bitcoin/testnet3/bitcoin.conf"
)
c.btc_network = "testnet"
_hash = "633de641ac179890b69c103fba76387ecaecd431a18e763a0d4764dbc1193031"
tx = c.rpc_getrawtransaction(_hash)
```

#### a hack into c.confirm_bitcoin_tx_local
```
from lntenna.txtenna_utilities.txtenna_segment import TxTennaSegment

r2 = c.btc_proxy.getrawtransaction(_hash, True)
confirmations = r2.get("confirmations", 0)
tn = True if c.btc_network is "testnet" else False
rObj = TxTennaSegment("", "", tx_hash=_hash, block=confirmations, testnet=tn)
c.send_private(gid=sender_gid, message=rObj.serialize_to_json())

result = {
    "send_status": {
        "Sent to GID": str(sender_gid),
        "txid": _hash,
        "status": "added to the mempool",
    }
}
if confirmations > 0:
    # send confirmations message back to tx sender if confirmations > 0
    rObj = TxTennaSegment("", "", tx_hash=_hash, block=confirmations)
    c.send_private(sender_gid, rObj.serialize_to_json())
    result["confirmation_status"] = {
        "transaction_from_gid": str(sender_gid),
        "txid": _hash,
        "status": "confirmed",
        "num_confirmations": confirmations,
    }
else:
    result["confirmation_status"] = {
        "transaction_from_gid": str(sender_gid),
        "txid": _hash,
        "status": "unconfirmed",
        "detail": "after 30 minutes",
    }
```

### remote api tests
```
api_req = {"type": "GET",
           "url": "https://api.blockstream.space/testnet/info"}
full_req = {"api_request": api_req}
import simplejson as json
json_req = json.dumps(full_req)
c.send_broadcast(message=json_req)
```