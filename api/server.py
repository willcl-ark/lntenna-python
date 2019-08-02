#!flask/bin/python

import logging

from flask import Flask
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api

from can_connect import CanConnect
from get_device_type import GetDeviceType
from get_connection_events import GetConnectionEvents
from get_system_info import GetSystemInfo
from list_geo_region import ListGeoRegion
from reset import Reset
from sdk_token import SdkToken
from send_broadcast import SendBroadcast
from set_geo_region import SetGeoRegion
from set_gid import SetGid

logger = logging.getLogger(__name__)
FORMAT = "[%(asctime)s - %(levelname)s] - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()
connection = None

api.add_resource(CanConnect, "/gotenna/api/v1.0/can_connect")
api.add_resource(GetConnectionEvents, "/gotenna/api/v1.0/get_connection_events")
api.add_resource(GetDeviceType, "/gotenna/api/v1.0/get_device_type")
api.add_resource(GetSystemInfo, "/gotenna/api/v1.0/get_system_info")
api.add_resource(ListGeoRegion, "/gotenna/api/v1.0/list_geo_region")
api.add_resource(Reset, "/gotenna/api/v1.0/reset")
api.add_resource(SdkToken, "/gotenna/api/v1.0/sdk_token")
api.add_resource(SendBroadcast, "/gotenna/api/v1.0/send_broadcast")
api.add_resource(SetGeoRegion, "/gotenna/api/v1.0/set_geo_region")
api.add_resource(SetGid, "/gotenna/api/v1.0/set_gid")

if __name__ == "__main__":
    app.run(debug=True)
