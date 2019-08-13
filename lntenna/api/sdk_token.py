#!flask/bin/python

from flask_restful import Resource, reqparse

import lntenna.server.config as config


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
        config.connection.sdk_token(sdk_token=args["sdk_token"])
        return {"sdk_token": config.connection.api_thread.sdk_token}
