#!flask/bin/python


from flask_restful import Resource, reqparse

import lntenna.server.config as config
from lntenna.gotenna.utilities import check_connection


class SetGeoRegion(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "region",
            type=int,
            required=True,
            help="Invalid or no region provided",
            location="json",
        )
        super(SetGeoRegion, self).__init__()

    @check_connection
    def post(self):
        args = self.reqparse.parse_args(strict=True)
        config.connection.set_geo_region(region=args["region"])
        return {
            "geo_region_set": config.connection.api_thread._settings.geo_settings.region
        }
