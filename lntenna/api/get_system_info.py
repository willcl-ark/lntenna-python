#!flask/bin/python

import logging
from flask_restful import Resource

import lntenna.server.config as config
from lntenna.gotenna_core.utilities import check_connection

logger = logging.getLogger(__name__)


class GetSystemInfo(Resource):
    def __init__(self):
        super(GetSystemInfo, self).__init__()

    @check_connection
    def get(self):
        logger.debug({"system_info": config.connection.get_system_info()})
        system_info = config.connection.get_system_info()
        # decode serial which is in bytes
        system_info["serial"] = system_info["serial"].decode('utf-8')
        logger.debug("system_info")
        return {"system_info": system_info}
