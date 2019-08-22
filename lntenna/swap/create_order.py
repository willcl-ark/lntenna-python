import logging

from blocksat_api import blocksat

import lntenna.database as db
from lntenna.server.config import CONFIG
from lntenna.swap.utilities import try_json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=CONFIG["logging"]["FORMAT"])


@try_json
def create_order(message: str, bid: str, network: str, uuid):
    logger.debug("Creating blocksat order")
    if network.strip().lower() == "testnet":
        satellite_url = CONFIG["blocksat"]["TESTNET_URL"]
    elif network.strip().lower() == "mainnet":
        satellite_url = CONFIG["blocksat"]["MAINNET_URL"]
    else:
        return {"response": "Invalid network"}
    db.orders_add_order(uuid=uuid, message=message, network=network)
    result = blocksat.place(message=message, bid=bid, satellite_url=satellite_url)
    if result.status_code == 200:
        try:
            db.satellite_add_quote(
                uuid=uuid, satellite_url=satellite_url, result=result.json()
            )
        except Exception as e:
            raise {"exception": e, "result": result}
    logging.debug(
        f"Successfully created blocksat order:\n{result.json()} using "
        f"satellite_url {satellite_url} and uuid {uuid}"
    )
    return {"response": result.json(), "uuid": uuid}
