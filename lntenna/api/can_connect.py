#!flask/bin/python

from flask_restful import Resource

import lntenna.server.config as config
from lntenna.gotenna.utilities import check_connection


class CanConnect(Resource):
    def __init__(self):
        super(CanConnect, self).__init__()

    @check_connection
    def get(self):
        return {"can_connect": config.connection.can_connect()}
