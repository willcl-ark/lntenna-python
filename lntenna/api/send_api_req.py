#!flask/bin/python

import ast
import logging

logger = logging.getLogger(__name__)

import simplejson as json
import requests
from flask_restful import Resource, reqparse

from lntenna.gotenna_core.utilities import prepare_api_request


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
        logger.debug(args)
        args["type"] = "POST"
        prepped = prepare_api_request(args)
        with requests.Session() as s:
            result = s.send(prepped, timeout=30)
        return result.text

    def get(self):
        args = self.reqparse.parse_args(strict=True)
        args["type"] = "GET"
        prepped = prepare_api_request(json.dumps(args))
        with requests.Session() as s:
            result = s.send(prepped, timeout=30)
        return result.text

    # def post(self):
    #     args = self.reqparse.parse_args(strict=True)
    #     args["type"] = "POST"
    #     req = requests.Request("POST")
    #     req.url = args["url"]
    #     req.headers = {} if args["headers"] is None else args["headers"]
    #     req.data = [] if args["data"] is None else ast.literal_eval(args["data"])
    #     req.params = {} if args["params"] is None else ast.literal_eval(args["params"])
    #     req.json = {} if args["json"] is None else ast.literal_eval(args["json"])
    #     prepped = req.prepare()
    #     result = self.session.send(prepped, timeout=30)
    #     return result.text
    #
    # def get(self):
    #     args = self.reqparse.parse_args(strict=True)
    #     req = requests.Request("GET")
    #     req.url = args["url"]
    #     req.headers = {} if args["headers"] is None else args["headers"]
    #     req.data = [] if args["data"] is None else ast.literal_eval(args["data"])
    #     req.params = {} if args["params"] is None else ast.literal_eval(args["params"])
    #     req.json = {} if args["json"] is None else ast.literal_eval(args["json"])
    #     prepped = req.prepare()
    #     result = self.session.send(prepped, timeout=30)
    #     return result.text
