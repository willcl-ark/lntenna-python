#!flask/bin/python

from flask_restful import Resource

import config
from utilities import check_connection


class GetDeviceType(Resource):
    def __init__(self):
        super(GetDeviceType, self).__init__()

    @check_connection
    def get(self):
        return {"device type": config.connection.get_device_type()}
