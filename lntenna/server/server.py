#!/usr/bin/env python3

"""lntenna API server

Usage:
    server.py [--debug] [--port PORT] [--no-api-server]

Options:
    -h --help    Show this screen

    -d --debug   Run in debug mode.

                 This will pull a second unique GID (DEBUG_GID) from config.ini and
                 attempt to configure settings for automatic GoTenna connection instead
                 of requiring manual setup from API calls.

    -p --port PORT
                 Port to run the REST API server on [default: 5000]

    -n --no-api-server
                 Disable the REST API server

"""

import logging
from time import sleep

from docopt import docopt
from flask import Flask
from flask_restful import Api

from lntenna.api import *
from lntenna.database import *
from lntenna.gotenna.connection import Connection
from lntenna.server.config import CONFIG
import lntenna.server.conn as g


g.CONN = Connection()

# setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=CONFIG["logging"]["FORMAT"])

# setup Flask REST API
app = Flask(__name__)
app.config["DEBUG"] = True
api = Api(app)

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

    if arguments["--debug"]:
        # setup the GoTenna Driver instance with settings from $HOME/.lntenna/config.ini
        try:
            g.CONN.sdk_token(CONFIG["gotenna"]["SDK_TOKEN"])
            g.CONN.set_gid(int(CONFIG["gotenna"]["DEBUG_GID"]))
            g.CONN.set_geo_region(int(CONFIG["gotenna"]["GEO_REGION"]))
        except Exception as e:
            raise e
    # check or create all db tables as necessary
    db.init()
    if arguments["--no-api-server"]:
        try:
            while True:
                sleep(60)
        except KeyboardInterrupt:
            print("\nExiting via KeyboardInterrupt")
    else:
        main(port=arguments["--port"])
