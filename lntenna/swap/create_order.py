import logging
from uuid import uuid4

from blocksat_api import blocksat
from lntenna.database import db
from lntenna.server.config import SATELLITE_API, TESTNET_SATELLITE_API, FORMAT
from lntenna.swap.utilities import try_json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=FORMAT)


@try_json
def create_order(message: str, bid: str, network: str):
    logger.debug("Creating blocksat order")
    if network.strip().lower() == "testnet":
        satellite_url = TESTNET_SATELLITE_API
    elif network.strip().lower() == "mainnet":
        satellite_url = SATELLITE_API
    else:
        return {"response": "Invalid network"}
    uuid = str(uuid4())[:8]
    db.add_order(uuid=uuid, message=message, network=network)
    result = blocksat.place(message=message, bid=bid, satellite_url=satellite_url)
    if result.status_code == 200:
        try:
            db.add_blocksat(
                uuid=uuid, satellite_url=satellite_url, result=result.json()
            )
        except Exception as e:
            raise {"exception": e, "result": result}
    logging.debug(f"Successfully created blocksat order:\n{result.json()} using "
    f"satellite_url {satellite_url} and uuid {uuid}")
    return {"response": result.json(), "uuid": uuid}
