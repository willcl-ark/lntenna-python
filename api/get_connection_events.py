#!flask/bin/python

from flask_restful import Resource

import config
from utilities import check_connection


class GetConnectionEvents(Resource):
    def __init__(self):
        super(GetConnectionEvents, self).__init__()

    @check_connection
    def get(self):
        return {"connection_events": config.connection.events.get_all_connection()}
