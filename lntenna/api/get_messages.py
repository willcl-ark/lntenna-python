#!flask/bin/python

from flask_restful import Resource

import lntenna.server.config as config
from lntenna.gotenna.utilities import check_connection


class GetMessages(Resource):
    def __init__(self):
        self.help = """Returns a list of all (text) messages received"""
        super(GetMessages, self).__init__()

    @check_connection
    def get(self):
        return {"message_events": config.connection.events.get_all_messages()}
