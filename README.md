# lntenna-python

In a terminal:
* create a python 3.6 venv and activate it

`pip install -r requirements.txt`

Open a python console for each GoTenna device and connect to it:

```python
import logging, simplejson as json
logging.basicConfig(level=logging.DEBUG)
from lntenna.gotenna import connection
c = connection.Connection()
c.sdk_token(
    sdk_token='your_sdk_token'
)
c.set_gid(gid='your_GID')
c.set_geo_region(region=2)
c.gateway = 1
```

To send a message, prepare the request and broadcast it:

```python
req = {"sat_req":
        {"m": "Hello, World, again!",
         "a": "your_bitcoin_refund_address_here",
         "n": "t"
         }
    }

c.send_broadcast(json.dumps(req))
```

`m`: message, 

`a`: refund address (in case swap is not fulfilled) and 

`n`: network (accepts "t" for testnet or "m" for mainnet)

Logging in each console will display the progress of the activity which is fully automatic until completion in this iteration.
