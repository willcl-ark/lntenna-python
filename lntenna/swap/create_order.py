from uuid import uuid4

from blocksat_api import blocksat
from lntenna.database import db
from lntenna.server.config import SATELLITE_API, TESTNET_SATELLITE_API
from lntenna.swap.utilities import try_json


@try_json
def create_order(message: str, bid: str, network: str):
    if network.strip().lower() == "testnet":
        satellite_url = TESTNET_SATELLITE_API
    elif network.strip().lower() == "mainnet":
        satellite_url = SATELLITE_API
    else:
        return {"response": "Invalid network"}
    print(satellite_url)
    uuid = str(uuid4())
    db.add_order(uuid=uuid, message=message, network=network)
    result = blocksat.place(message=message, bid=bid, satellite_url=satellite_url)
    if result.status_code == 200:
        try:
            db.add_blocksat(
                uuid=uuid, satellite_url=satellite_url, result=result.json()
            )
        except Exception as e:
            raise {"exception": e, "result": result}
    return {"response": result.json(),
            "uuid": uuid}
