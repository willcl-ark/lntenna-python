# lntenna

In a terminal:
* create a python 3.6 venv and activate it

`pip install -r requirements.txt`

`python lntenna/server/server.py`

## API tests
In a python console:

```python
import requests, time
from pprint import pprint
import simplejson as json

url = "http://127.0.0.1:5000"
s = requests.Session()
```

#### SDK test
```python
sdk_params = {
    "sdk_token": "H18BVEYPTAAEVAFEXgIOFUECAgNHUlgDB0APAgFREB0BWRcIAkdRQAAHXgUOUAxc"
}
sdk_test = s.post(url=url + "/gotenna/api/v1.0/sdk_token", json=sdk_params)
pprint(sdk_test.json())
```

#### reset connection vars test
`reset_test = s.get(url=url + '/gotenna/api/v1.0/reset')`

#### set gid
```python
gid_params = {"gid": 87654321}
gid_test = s.post(url=url + "/gotenna/api/v1.0/set_gid", json=gid_params)
pprint(gid_test.json())
```

#### set geo region
```python
geo_params = {"region": 2}
geo_test = s.post(url=url + "/gotenna/api/v1.0/set_geo_region", json=geo_params)
pprint(geo_test.json())
```

* power on goTenna!

#### send_broadcast
```python
msg_params = {"message": "Hello, world!"}
broadcast_test = s.post(url=url + "/gotenna/api/v1.0/send_broadcast", json=msg_params)
pprint(broadcast_test.json())
```

#### get_device_type
```python
device_type = s.get(url=url + "/gotenna/api/v1.0/get_device_type")
pprint(device_type.json())
```

#### list geo_regions
```python
avail_regions = s.get(url=url + "/gotenna/api/v1.0/list_geo_region")
pprint(avail_regions.json())
```

#### get can_connect
```python
can_connect = s.get(url=url + "/gotenna/api/v1.0/can_connect")
pprint(can_connect.json())
```

#### retrieve stored connection events
```python
connection_events = s.get(url=url + "/gotenna/api/v1.0/get_connection_events")
pprint(connection_events.json())
```

#### get_system_info
```python
system_info = s.get(url=url + "/gotenna/api/v1.0/get_system_info")
pprint(system_info.json())
```

#### retrieve all messages received by the device
```python
message_events = s.get(url=url + "/gotenna/api/v1.0/get_messages")
pprint(message_events.json())
```

#### test api_request
```python
post_test1 = {
    "api_request": {"url": "https://api.blockstream.space/testnet/info", "type": "GET"}
}
post_api_call1 = s.post(url=url + "/gotenna/api/v1.0/api_request", json=post_test1)
post_api_call1.json()

post_data = {"message": "test_msg", "bid": 10000}
post_test = {
    "api_request": {
        "url": "https://api.blockstream.space/testnet/order",
        "data": json.dumps(post_data),
        "type": "POST",
    }
}
post_api_call = s.post(url=url + "/gotenna/api/v1.0/api_request", json=post_test)
post_api_call.json()
```

## txtenna tests

#### configure bitcoin params
```python
btc_config = {
    "btc_conf_file": "/Users/will/Library/Application Support/Bitcoin/testnet3/bitcoin.conf",
    "btc_network": "testnet",
}
configure_bitcoin = s.post(url=url + "/bitcoin/api/v1.0/configure", json=btc_config)
```

#### getrawtransaction
```python
getrawtx = {"tx_id": "633de641ac179890b69c103fba76387ecaecd431a18e763a0d4764dbc1193031"}
raw_tx_test = s.get(url=url + "/bitcoin/api/v1.0/rpc_getrawtransaction", json=getrawtx)
raw_tx_data = raw_tx_test.json()

raw_proxy_json = {"command": "getbalance", "args": None}
raw_proxy_test = s.post(url=url + "/bitcoin/api/v1.0/rpc_rawproxy", json=raw_proxy_json)
print(raw_proxy_test.json())

raw_proxy_json2 = {
    "command": "getrawtransaction",
    "args": ["633de641ac179890b69c103fba76387ecaecd431a18e763a0d4764dbc1193031", True],
}
raw_proxy_test2 = s.post(
    url=url + "/bitcoin/api/v1.0/rpc_rawproxy", json=raw_proxy_json2
)
print(raw_proxy_test2.json())
```


#### GetAPI call
* make sure server is running with --gateway flag
* see lntenna/api/server.py L60
```python
api_req = {"type": "GET", "url": "https://api.blockstream.space/testnet/info"}
full_req = {"api_request": api_req}
api_test = s.post(url=url + "/gotenna/api/v1.0/api_request", json=full_req)
```

## manual equivalents

```python
from lntenna.gotenna import connection
from goTenna.settings import GID

c = connection.Connection()
c.sdk_token(
    sdk_token="H18BVEYPTAAEVAFEXgIOFUECAgNHUlgDB0APAgFREB0BWRcIAkdRQAAHXgUOUAxc"
)
c.set_gid(gid=12345678)
c.set_geo_region(region=2)
```

* power on goTenna

```python
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

### txtenna
```python
c.btc_network = "testnet"
_hash = "633de641ac179890b69c103fba76387ecaecd431a18e763a0d4764dbc1193031"
tx = c.rpc_getrawtransaction(_hash)
```

* a hack into c.confirm_bitcoin_tx_local
```python
from lntenna.txtenna.txtenna_segment import TxTennaSegment

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
```python
api_req = {"type": "GET", "url": "https://api.blockstream.space/testnet/info"}
full_req = {"api_request": api_req}
import simplejson as json

json_req = json.dumps(full_req)
c.send_broadcast(message=json_req)
```

# swap system

```python
import time
import lntenna.swap as s
```

#### create a message

```python
msg = s.create_random_message()
```

#### get swap rates
```python
rates = s.swap_rates()
```

* TODO: get blocksat order rates and use them to calculate / size?

#### create a blocksat order
```python
blocksat_order = s.create_order(message=msg, bid="10000", network="testnet")
```

#### lookup the invoice received on the swap server to check payable
```python
invoice_lookup = s.get_invoice_details(
    invoice=blocksat_order["response"]["lightning_invoice"]["payreq"], network="testnet"
)
```

#### generate a refund address and check it with the swap server
```python
refund_addr = s.get_refund_address(uuid=blocksat_order["uuid"], addr_type="legacy")
assert s.get_address_details(refund_addr, 'testnet').status_code == 200

swap = s.get_swap_quote(uuid=blocksat_order["uuid"], invoice=blocksat_order["response"]["lightning_invoice"]["payreq"], network='testnet')
```

#### decode the invoice
```python
from lntenna.lightning.lnaddr import lndecode

# attempt decode, raise value error if signature mismatch
decoded_inv = lndecode(blocksat_order["response"]["lightning_invoice"]["payreq"])
```

#### Check the Pubkey from the invoice matches pre-known keys

This key might be supplied with invoice, or derived from signature, it doesn't matter.
```python
from lntenna.server.config import BLOCKSAT_NODE_PUBKEYS
from binascii import hexlify

assert hexlify(decoded_inv.pubkey.serialize()).decode("utf-8") in BLOCKSAT_NODE_PUBKEYS
```

#### check the redeem_script matches the lightning invoice payment_hash
```python
assert s.compare_redeemscript_invoice(blocksat_order["response"]["lightning_invoice"]["rhash"], swap["response"]["redeem_script"])
```

#### pay the swap using bitcoind
```python
pay_swap = s.pay_swap(uuid=blocksat_order["uuid"])
```

#### check for swap preimage denoting payment
```python
while True:
    check_swap_status = s.check_swap(uuid=blocksat_order["uuid"])
    if "response" in check_swap_status:
        if "payment_secret" in check_swap_status["response"]:
            break
    time.sleep(5)
```
