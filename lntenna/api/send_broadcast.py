#!flask/bin/python

import logging

from flask_restful import Resource, reqparse

import lntenna.api.config as config
from lntenna.gotenna_core.utilities import wait_for, check_connection

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

    @check_connection
    def post(self):
        args = self.reqparse.parse_args(strict=True)
        evt_start_len = config.connection.events.callback.qsize()
        logger.debug("send_broadcast evt_start_len is {}".format(evt_start_len))
        config.connection.send_broadcast(message=args["message"])
        wait_for(lambda: config.connection.events.callback.qsize() > evt_start_len)
        result = []
        while config.connection.events.callback.qsize() > evt_start_len:
            result.append(config.connection.events.callback.get())
        return {"send_broadcast": result}
