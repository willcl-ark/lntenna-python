#!flask/bin/python

import ast
import requests
from flask_restful import Resource, reqparse

from lntenna.gotenna_core.utilities import prepare_api_request


class ApiRequest(Resource):
    """All api requests are called via 'POST'

    Takes a single json field, which should contain json
    representation of the request in dict of the form:

    json = {
        "api_request": {
            "type": "POST",
            "url": "www.xyz.com/api/v1.0/order",
            "params": {"param_1": "start_time=1"},
            "headers": {"header_1": "header"},
            "data": {"data_1": "some_data"},
            "json": {"json_data": {"json_stuff": "data"}},
        }
    }
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "api_request", required=False, help="api_request", location="json"
        )
        super(ApiRequest, self).__init__()

    def post(self):
        args = self.reqparse.parse_args(strict=True)
        api_request = ast.literal_eval(args.api_request)
        prepped = prepare_api_request(api_request)
        with requests.Session() as s:
            result = s.send(prepped, timeout=30)
        return result.text
