#!flask/bin/python

import logging

from flask import Flask
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api

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

api.add_resource(Reset, "/gotenna/api/v1.0/reset")
api.add_resource(SdkToken, "/gotenna/api/v1.0/sdk_token")
api.add_resource(SendBroadcast, "/gotenna/api/v1.0/send_broadcast")
api.add_resource(SetGeoRegion, "/gotenna/api/v1.0/set_geo_region")
api.add_resource(SetGid, "/gotenna/api/v1.0/set_gid")

if __name__ == "__main__":
    app.run(debug=True)
