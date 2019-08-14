#!flask/bin/python

from flask_restful import Resource

import lntenna.server.config as config
from lntenna.gotenna.utilities import check_connection


class GetSystemInfo(Resource):
    def __init__(self):
        super(GetSystemInfo, self).__init__()

    @check_connection
    def get(self):
        system_info = config.connection.get_system_info()
        # decode serial which is in bytes
        system_info["serial"] = system_info["serial"].decode("utf-8")
        return {"system_info": system_info}
