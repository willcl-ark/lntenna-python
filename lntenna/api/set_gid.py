#!flask/bin/python

import logging

from flask_restful import Resource, reqparse

import lntenna.server.config as config
from lntenna.gotenna.utilities import check_connection

logger = logging.getLogger(__name__)
FORMAT = "[%(asctime)s - %(levelname)s] - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)


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
        logger.debug("GID set as {}".format(config.connection.api_thread.gid._gid_val))
        return {"gid": config.connection.api_thread.gid._gid_val}
