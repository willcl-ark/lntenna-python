#!flask/bin/python

from flask_restful import Resource, reqparse

import lntenna.server.conn as g
from lntenna.gotenna.utilities import check_connection, wait_for


class SendBroadcast(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "message",
            type=str,
            required=True,
            help="Invalid or no message provided",
            location="json",
        )
        super(SendBroadcast, self).__init__()

    @check_connection
    def post(self):
        args = self.reqparse.parse_args(strict=True)
        evt_start_len = g.CONN.events.callback.qsize()
        g.CONN.send_broadcast(message=args["message"])
        wait_for(lambda: g.CONN.events.callback.qsize() > evt_start_len)
        result = []
        while g.CONN.events.callback.qsize() > evt_start_len:
            result.append(g.CONN.events.callback.get())
        return {"send_broadcast": result}
