from uuid import uuid4

from blocksat_api import blocksat
from lntenna.database import db
from lntenna.server.config import SATELLITE_API, TESTNET_SATELLITE_API


def create_order(message: str, bid: str, network: str):
    if network.strip().lower() == "testnet":
        satellite_url = TESTNET_SATELLITE_API
    elif network.strip().lower() == "mainnet":
        satellite_url = SATELLITE_API
    else:
        return "Invalid network"
    print(satellite_url)
    uuid = uuid4()
    db.add_order(uuid=str(uuid), message=message, network=network)
    result = blocksat.place(message=message, bid=bid, satellite_url=satellite_url)
    if result.status_code == 200:
        try:
            db.add_blocksat(
                uuid=str(uuid), satellite_url=satellite_url, result=result.json()
            )
            db_status = "added to db"
        except Exception as e:
            db_status = "not added to db"
            raise {"exception": e, "result": result}
    else:
        db_status = "not added to db"

    try:
        response = result.json()
        code = 200
    except (ValueError, KeyError):
        response = result.text
        code = result.status_code
    return {"order": response, "uuid": str(uuid), "code": code, "db_status": db_status}
