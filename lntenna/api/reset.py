#!flask/bin/python

from flask_restful import Resource

import lntenna.api.config as config
import goTenna
from lntenna.gotenna_core.utilities import check_connection


class Reset(Resource):
    def __init__(self):
        super(Reset, self).__init__()

    @check_connection
    def get(self):
        if hasattr(config.connection, "api_thread") and isinstance(
            config.connection.api_thread, goTenna.driver.Driver
        ):
            config.connection.reset()
            status = "Connection and SDK token successfully reset"
        else:
            status = "No api_thread.sdk_token detected, nothing to reset"
        return {"reset": status}
