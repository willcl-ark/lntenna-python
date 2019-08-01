#!flask/bin/python

from flask_restful import Api, Resource, reqparse

import config
import goTenna


class Reset(Resource):
    def __init__(self):
        super(Reset, self).__init__()

    def post(self):
        if config.connection is None:
            status = "Connection not initialised, nothing to reset"
        elif hasattr(config.connection, "api_thread") and isinstance(
            config.connection.api_thread, goTenna.driver.Driver
        ):
            config.connection.reset()
            status = "Connection and SDK token successfully reset"
        else:
            status = "No api_thread.sdk_token detected, nothing to reset"
        return {"reset": status}
