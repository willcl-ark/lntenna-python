from lntenna.server.config import SUBMARINE_API
from lntenna.database import db
import submarine_api


def get_swap_quote(uuid: str, invoice: str, network: str):
    refund_address = db.lookup_refund_addr(uuid)[0]
    result = submarine_api.get_quote(
        url=SUBMARINE_API, network=network, invoice=invoice, refund=refund_address
    )
    # add the swap to the swap table
    db.add_swap(uuid=uuid, result=result.json())
    return {"result": result.text, "status_code": result.status_code}
