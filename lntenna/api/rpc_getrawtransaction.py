#!flask/bin/python

from flask_restful import Resource, reqparse
import simplejson

import lntenna.server.config as config
from lntenna.gotenna_core.utilities import check_connection


class RpcGetrawtransaction(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "tx_id",
            type=str,
            required=True,
            help="Invalid or no txid provided. Requires little endian hex encoding.",
            location="json",
        )
        super(RpcGetrawtransaction, self).__init__()

    @check_connection
    def get(self):
        args = self.reqparse.parse_args(strict=True)
        tx = simplejson.dumps(
                config.connection.rpc_getrawtransaction(
                        args["tx_id"]
                )
        )
        return {"transaction": tx}
