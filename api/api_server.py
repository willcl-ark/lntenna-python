#!flask/bin/python

import json

from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields, marshal
from flask_httpauth import HTTPBasicAuth

from network import *

app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()
connection = None


def handle_event(evt):
    return {
        '__str__': evt.__str__(),
        'event_type': evt.event_type,
        'message': evt.message,
        'status': evt.status,
        'device_details': evt.device_details,
        'disconnect_code': evt.disconnect_code,
        'disconnect_reason': evt.disconnect_reason,
        'group': evt.group,
        'device_paths': evt.device_paths
    }


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
        global connection
        args = self.reqparse.parse_args(strict=True)
        connection = Connection()
        connection.sdk_token(sdk_token=args["sdk_token"])
        tries = 20
        while connection.device_present_events.qsize() == 0 and tries < 20:
            sleep(1)
        return handle_event(connection.device_present_events.get())


api.add_resource(SdkToken, "/gotenna/api/v1.0/sdk_token")

if __name__ == "__main__":
    app.run(debug=True)
