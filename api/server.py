#!flask/bin/python

from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields, marshal
from flask_httpauth import HTTPBasicAuth

from reset import Reset
from set_gid import SetGid
from sdk_token import SdkToken

app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()
connection = None


api.add_resource(Reset, "/gotenna/api/v1.0/reset")
api.add_resource(SetGid, "/gotenna/api/v1.0/set_gid")
api.add_resource(SdkToken, "/gotenna/api/v1.0/sdk_token")

if __name__ == "__main__":
    app.run(debug=True)
