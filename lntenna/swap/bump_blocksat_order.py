from blocksat_api import blocksat
from lntenna.database import db


def bump_blocksat_order(uuid: str, bid_increase: str):
    # lookup the order from blocksat table
    blocksat_uuid, auth_token, satellite_url = db.lookup_bump(uuid=uuid)
    # bump the order using the details
    result = blocksat.bump_order(
            uuid=blocksat_uuid,
            auth_token=auth_token,
            bid_increase=bid_increase,
            satellite_url=satellite_url,
    )
    return {"result": result.text,
            "code": result.status_code}
