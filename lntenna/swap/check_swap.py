from lntenna.database import db
from lntenna.server.config import SUBMARINE_API
import submarine_api


def check_swap(uuid: str):
    # lookup swap details here
    network, invoice, redeem_script = db.lookup_swap_details(uuid)
    result = submarine_api.check_status(
        url=SUBMARINE_API, network=network, invoice=invoice, redeem_script=redeem_script
    )
    return {"result": result.text, "status_code": result.status_code}
