#!flask/bin/python

from flask_restful import Resource

import lntenna.server.conn as g
from lntenna.gotenna.utilities import check_connection


class GetMessages(Resource):
    def __init__(self):
        self.help = """Returns a list of all (text) messages received"""
        super(GetMessages, self).__init__()

    @check_connection
    def get(self):
        return {"message_events": g.CONN.events.get_all_messages()}
