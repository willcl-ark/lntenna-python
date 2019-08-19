#!flask/bin/python

"""lntenna API server

Usage:
    server.py [--gateway] [--port PORT]

Options:
    -h --help    Show this screen
    --gateway    Whether to run in gateway mode with online connection
    --port PORT  Port to run the server on [default: 5000]

"""

import logging

from docopt import docopt
from flask import Flask
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api

import lntenna.server.config as config
from lntenna.api import *
from lntenna.database import *
from lntenna.gotenna.connection import Connection
from lntenna.server.config import FORMAT

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

app = Flask(__name__)
app.config["DEBUG"] = True
api = Api(app)
auth = HTTPBasicAuth()
config.connection = Connection()

api.add_resource(ApiRequest, "/gotenna/api/v1.0/api_request")
api.add_resource(CanConnect, "/gotenna/api/v1.0/can_connect")
api.add_resource(GetConnectionEvents, "/gotenna/api/v1.0/get_connection_events")
api.add_resource(GetDeviceType, "/gotenna/api/v1.0/get_device_type")
api.add_resource(GetMessages, "/gotenna/api/v1.0/get_messages")
api.add_resource(GetSystemInfo, "/gotenna/api/v1.0/get_system_info")
api.add_resource(ListGeoRegion, "/gotenna/api/v1.0/list_geo_region")
api.add_resource(Reset, "/gotenna/api/v1.0/reset")
api.add_resource(RpcRawProxy, "/bitcoin/api/v1.0/rpc_rawproxy")
api.add_resource(SdkToken, "/gotenna/api/v1.0/sdk_token")
api.add_resource(SendBroadcast, "/gotenna/api/v1.0/send_broadcast")
api.add_resource(SetGeoRegion, "/gotenna/api/v1.0/set_geo_region")
api.add_resource(SetGid, "/gotenna/api/v1.0/set_gid")


def main(port):
    app.run(port=port)


if __name__ == "__main__":
    arguments = docopt(__doc__)
    print(arguments)
    if arguments["--gateway"]:
        config.connection.gateway = 1
    db.init()
    main(port=arguments["--port"])
