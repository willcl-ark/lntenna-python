#!flask/bin/python

from flask_restful import Resource, reqparse

import config
from network import Connection
from utilities import handle_event, wait_for


class SdkToken(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "sdk_token",
            type=str,
            required=True,
            help="Invalid or no SDK token provided",
            location="json",
        )
        super(SdkToken, self).__init__()

    def post(self):
        args = self.reqparse.parse_args(strict=True)
        config.connection = Connection()
        config.connection.sdk_token(sdk_token=args["sdk_token"])
        wait_for(lambda: config.connection.device_present_events.qsize() != 0)
        return handle_event(config.connection.device_present_events.get())
