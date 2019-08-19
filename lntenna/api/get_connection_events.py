#!flask/bin/python

from flask_restful import Resource

import lntenna.server.conn as g
from lntenna.gotenna.utilities import check_connection


class GetConnectionEvents(Resource):
    def __init__(self):
        self.help = """Returns a dictionary containing all connect, disconnect and 
        device_present messages received by the driver"""
        super(GetConnectionEvents, self).__init__()

    @check_connection
    def get(self):
        return {"connection_events": g.CONN.events.get_all_connection()}
