#!flask/bin/python

from flask_restful import Resource

import lntenna.server.conn as g
from lntenna.gotenna.utilities import check_connection


class GetDeviceType(Resource):
    def __init__(self):
        super(GetDeviceType, self).__init__()

    @check_connection
    def get(self):
        return {"device type": g.CONN.get_device_type()}
