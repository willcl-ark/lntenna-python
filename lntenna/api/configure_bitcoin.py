#!flask/bin/python

from flask_restful import Resource, reqparse

import lntenna.server.config as config
from lntenna.gotenna.utilities import check_connection


class ConfigureBitcoin(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "btc_conf_file",
            type=str,
            required=True,
            help="bitcoin.conf path",
            location="json",
        )
        self.reqparse.add_argument(
            "btc_network",
            type=str,
            required=True,
            help="mainnet, testnet or regtest",
            location="json",
        )
        super(ConfigureBitcoin, self).__init__()

    @check_connection
    def post(self):
        args = self.reqparse.parse_args(strict=True)
        config.connection.btc_conf_file = args["btc_conf_file"]
        config.connection.btc_network = args["btc_network"]
        return {
            "btc_conf_file": config.connection.btc_conf_file,
            "btc_network": config.connection.btc_network,
        }
