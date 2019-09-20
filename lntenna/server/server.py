#!/usr/bin/env python3

"""lntenna API server

Usage:
    python server.py
"""

import logging
from time import sleep

from lntenna.database import *
from lntenna.gotenna.connection import Connection
from lntenna.server.config import CONFIG
import lntenna.server.conn as g


g.CONN = Connection()

# setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=CONFIG["logging"]["FORMAT"])


def main():

    # setup the GoTenna Driver instance with settings from $HOME/.lntenna/config.ini
    logger.debug("Configuring goTenna Device attributes from $HOME/.lntenna/config.ini")
    try:
        g.CONN.sdk_token(CONFIG["gotenna"]["SDK_TOKEN"])
        g.CONN.set_gid(int(CONFIG["gotenna"]["DEBUG_GID"]))
        g.CONN.set_geo_region(int(CONFIG["gotenna"]["GEO_REGION"]))
    except Exception as e:
        raise e

    # check or create all db tables as necessary
    logger.debug("Checking database in $HOME/.lntenna/database.db")
    db.init()

    # simple loop until KeyboardInterrupt
    logger.debug("Server started. Use Ctrl+C to stop")
    try:
        while True:
            sleep(60)
    except KeyboardInterrupt:
        print("\nExiting via KeyboardInterrupt")


if __name__ == "__main__":
    main()
