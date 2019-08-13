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

import lntenna.api.config as config
from can_connect import CanConnect
from configure_bitcoin import ConfigureBitcoin
from get_device_type import GetDeviceType
from get_connection_events import GetConnectionEvents
from get_messages import GetMessages
from get_system_info import GetSystemInfo
from list_geo_region import ListGeoRegion
from lntenna.gotenna_core.connection import Connection
from reset import Reset
from rpc_getrawtransaction import RpcGetrawtransaction
from rpc_rawproxy import RpcRawProxy
from sdk_token import SdkToken
from send_api_req import ApiRequest
from send_broadcast import SendBroadcast
from set_geo_region import SetGeoRegion
from set_gid import SetGid

logger = logging.getLogger(__name__)
FORMAT = "[%(asctime)s - %(levelname)s] - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()
config.connection = Connection()


api.add_resource(ApiRequest, "/gotenna/api/v1.0/api_request")
api.add_resource(CanConnect, "/gotenna/api/v1.0/can_connect")
api.add_resource(ConfigureBitcoin, "/bitcoin/api/v1.0/configure")
api.add_resource(GetConnectionEvents, "/gotenna/api/v1.0/get_connection_events")
api.add_resource(GetDeviceType, "/gotenna/api/v1.0/get_device_type")
api.add_resource(GetMessages, "/gotenna/api/v1.0/get_messages")
api.add_resource(GetSystemInfo, "/gotenna/api/v1.0/get_system_info")
api.add_resource(ListGeoRegion, "/gotenna/api/v1.0/list_geo_region")
api.add_resource(Reset, "/gotenna/api/v1.0/reset")
api.add_resource(RpcGetrawtransaction, "/bitcoin/api/v1.0/rpc_getrawtransaction")
api.add_resource(RpcRawProxy, "/bitcoin/api/v1.0/rpc_rawproxy")
api.add_resource(SdkToken, "/gotenna/api/v1.0/sdk_token")
api.add_resource(SendBroadcast, "/gotenna/api/v1.0/send_broadcast")
api.add_resource(SetGeoRegion, "/gotenna/api/v1.0/set_geo_region")
api.add_resource(SetGid, "/gotenna/api/v1.0/set_gid")


def main(port):
    app.run(debug=True, port=port)


if __name__ == "__main__":
    arguments = docopt(__doc__)
    print(arguments)
    if arguments["--gateway"]:
        config.connection.gateway = 1
    main(port=arguments["--port"])
