#!flask/bin/python

from flask_restful import Resource, reqparse

import lntenna.server.conn as g
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
        g.CONN.api_thread.set_gid(None)
        # set new gid
        g.CONN.set_gid(gid=args["gid"])
        return {"gid": g.CONN.api_thread.gid._gid_val}
