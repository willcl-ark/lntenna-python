#!flask/bin/python


from flask_restful import Resource, reqparse

import lntenna.server.config as config
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
        evt_start_len = config.connection.events.callback.qsize()
        config.connection.send_broadcast(message=args["message"])
        wait_for(lambda: config.connection.events.callback.qsize() > evt_start_len)
        result = []
        while config.connection.events.callback.qsize() > evt_start_len:
            result.append(config.connection.events.callback.get())
        return {"send_broadcast": result}
