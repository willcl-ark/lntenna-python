#!flask/bin/python

import goTenna
from flask_restful import Resource

import lntenna.server.conn as g
from lntenna.gotenna.utilities import check_connection


class Reset(Resource):
    def __init__(self):
        self.help = """Attempts to flush the driver and SDK token to allow reset without
         restarting the server. Not always successful so check success."""
        super(Reset, self).__init__()

    @check_connection
    def get(self):
        if hasattr(g.CONN, "api_thread") and isinstance(
            g.CONN.api_thread, goTenna.driver.Driver
        ):
            g.CONN.reset()
            status = "Connection and SDK token successfully reset"
        else:
            status = "No api_thread.sdk_token detected, nothing to reset"
        return {"reset": status}
