#!flask/bin/python

from flask_restful import Resource

import lntenna.api.config as config
from lntenna.gotenna_core.utilities import check_connection


class GetSystemInfo(Resource):
    def __init__(self):
        super(GetSystemInfo, self).__init__()

    @check_connection
    def get(self):
        return {"system_info": config.connection.get_system_info()}
