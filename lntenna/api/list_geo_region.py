#!flask/bin/python

from flask_restful import Resource

import lntenna.server.conn as g
from lntenna.gotenna.utilities import check_connection


class ListGeoRegion(Resource):
    def __init__(self):
        super(ListGeoRegion, self).__init__()

    @check_connection
    def get(self):
        return {"allowed_geo_regions": g.CONN.list_geo_region()}
