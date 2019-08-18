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
         "a": "mut6HiwhKab6csGyUBbacoHDq7BvENVti8",
         "n": "t"
         }
    }

c.send_broadcast(json.dumps(req))
```

Logging in each console will display the progress of the activity.
