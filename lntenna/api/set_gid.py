#!flask/bin/python

from flask_restful import Resource, reqparse

import lntenna.server.config as config
from lntenna.gotenna.utilities import check_connection


class SetGid(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "gid",
            type=int,
            required=True,
            help="Invalid or no GID provided",
            location="json",
        )
        super(SetGid, self).__init__()

    @check_connection
    def post(self):
        args = self.reqparse.parse_args(strict=True)
        # purge existing GID
        config.connection.api_thread.set_gid(None)
        # set new gid
        config.connection.set_gid(gid=args["gid"])
        return {"gid": config.connection.api_thread.gid._gid_val}
