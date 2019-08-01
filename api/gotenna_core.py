import threading

from flask import jsonify, make_response
from flask_restful import Resource, reqparse

import goTenna
from network import Connection

from utilities.segment_storage import SegmentStorage


class Initialize(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("sdk_token", type=str, location="json")
        self.reqparse.add_argument("gid", type=int, location="json")
        super(Initialize, self).__init__()

    def put(self):
        args = self.reqparse.parse_args(strict=True)
        connection = threading.Thread(name=args["sdk_token"])
        # TODO: SPI_CONNECTION stuff removed
        try:
            connection.api = goTenna.driver.Driver(
                sdk_token=args["sdk_token"],
                gid=args["gid"],
                settings=None,
                event_callback=self.event_callback,
            )
            connection.api.start()
        except ValueError:
            print(
                "SDK token {} is not valid. Please enter a valid SDK token.".format(
                    args["sdk_token"]
                )
            )
