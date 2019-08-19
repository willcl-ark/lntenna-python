#!flask/bin/python

from flask_restful import Resource, reqparse

import lntenna.server.conn as g


class SdkToken(Resource):
    def __init__(self):
        self.help = """Sets the SDK token of the server's connection instance"""
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
        g.CONN.sdk_token(sdk_token=args["sdk_token"])
        return {"sdk_token": g.CONN.api_thread.sdk_token.decode("utf-8")}
