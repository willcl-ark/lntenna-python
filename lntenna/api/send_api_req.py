#!flask/bin/python

import ast

import requests
from flask_restful import Resource, reqparse


class ApiRequest(Resource):
    def __init__(self):
        self.session = requests.Session()
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "url", type=str, required=True, help="web address to query", location="json"
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
            "data", required=False, help="data to pass form data", location="json"
        )
        self.reqparse.add_argument(
            "json", required=False, help="json data", location="json"
        )
        super(ApiRequest, self).__init__()

    def post(self):
        args = self.reqparse.parse_args(strict=True)
        req = requests.Request("POST")
        req.url = args["url"]
        req.headers = {} if args["headers"] is None else args["headers"]
        req.data = [] if args["data"] is None else ast.literal_eval(args["data"])
        req.params = {} if args["params"] is None else ast.literal_eval(args["params"])
        req.json = {} if args["json"] is None else ast.literal_eval(args["json"])
        prepped = req.prepare()
        result = self.session.send(prepped, timeout=30)
        return result.text

    def get(self):
        args = self.reqparse.parse_args(strict=True)
        req = requests.Request("GET")
        req.url = args["url"]
        req.headers = {} if args["headers"] is None else args["headers"]
        req.data = [] if args["data"] is None else ast.literal_eval(args["data"])
        req.params = {} if args["params"] is None else ast.literal_eval(args["params"])
        req.json = {} if args["json"] is None else ast.literal_eval(args["json"])
        prepped = req.prepare()
        result = self.session.send(prepped, timeout=30)
        return result.text
