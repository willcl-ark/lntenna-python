#!flask/bin/python

import requests
from flask_restful import Resource, reqparse


class ApiRequest(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "url",
            type=str,
            required=True,
            help="web address to query",
            location="json",
        )
        self.reqparse.add_argument(
            "params",
            type=dict,
            required=False,
            help="params to append to the url",
            location="json",
        )
        self.reqparse.add_argument(
            "headers",
            type=dict,
            required=False,
            help="headers to add to the url",
            location="json",
        )
        self.reqparse.add_argument(
            "data",
            required=False,
            help="data to pass form data",
            location="json",
        )
        super(ApiRequest, self).__init__()

    def post(self):
        args = self.reqparse.parse_args(strict=True)
        r = requests.post(
                url=args["url"],
                params=args["params"],
                headers=args["headers"],
                data=args["data"],
                timeout=30
        )
        return r.text
