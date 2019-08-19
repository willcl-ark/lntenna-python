#!flask/bin/python

import simplejson as json
from flask_restful import Resource, reqparse

import lntenna.server.config as config
from lntenna.gotenna.utilities import check_connection
from lntenna.swap import auto_swap_create


class AutoSatSwap(Resource):
    def __init__(self):
        self.help = """Takes a json encoded dict as argument with keys: 
        "m" - message, "a" - refund address and "n" - network """
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "json_request", required=False, help=self.help, location="json"
        )
        super(AutoSatSwap, self).__init__()

    @check_connection
    def post(self):
        args = self.reqparse.parse_args(strict=True)
        # return the request to a dict
        request = json.loads(args.json_request)
        # setup the blocksat quote and swap quote
        quotes = json.dumps(auto_swap_create(request))
        # broadcast the result back to sender
        config.connection.send_jumbo(quotes)
        return
