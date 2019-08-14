#!flask/bin/python

import ast
import simplejson
from flask_restful import Resource, reqparse

import lntenna.server.config as config
from lntenna.gotenna.utilities import check_connection


class RpcRawProxy(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "command",
            type=str,
            required=True,
            help="bitcoind rpc command to run via python-bitcoinlib's RawProxy.",
            location="json",
        )
        self.reqparse.add_argument(
            "args",
            type=str,
            required=False,
            help="args to be provided in required order as a string",
            location="json",
        )
        super(RpcRawProxy, self).__init__()

    @check_connection
    def post(self):
        args = self.reqparse.parse_args(strict=True)
        if args["args"] is "null":
            result = simplejson.dumps(
                getattr(config.connection.btc_proxy, args["command"])
            )
        else:
            args["args"] = ast.literal_eval(args["args"])
            result = simplejson.dumps(
                getattr(config.connection.btc_proxy, args["command"])(*args["args"])
            )
        return {args["command"]: result}
