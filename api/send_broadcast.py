#!flask/bin/python

import logging

from flask_restful import Resource, reqparse

import config
from utilities import handle_event, wait_for

logger = logging.getLogger(__name__)
FORMAT = "[%(asctime)s - %(levelname)s] - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)


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

    def post(self):
        args = self.reqparse.parse_args(strict=True)
        config.connection.send_broadcast(message=args["message"])




        # logger.debug(
        #     "Region set as {}".format(
        #         config.connection.api_thread._settings.geo_settings.region
        #     )
        # )
        return {}