#!flask/bin/python

from flask_restful import Resource

import lntenna.api.config as config
from lntenna.gotenna_core.utilities import check_connection


class ListGeoRegion(Resource):
    def __init__(self):
        super(ListGeoRegion, self).__init__()

    @check_connection
    def get(self):
        return {"allowed_geo_regions": config.connection.list_geo_region()}
