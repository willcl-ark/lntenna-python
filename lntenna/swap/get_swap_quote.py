from lntenna.server.config import SUBMARINE_API
from lntenna.database import db
import submarine_api
from lntenna.swap.utilities import try_json


@try_json
def get_swap_quote(uuid: str, invoice: str, network: str, refund_addr: str):
    result = submarine_api.get_quote(
        url=SUBMARINE_API, network=network, invoice=invoice, refund=refund_addr
    )
    # add the swap to the swap table
    db.add_swap(uuid=uuid, result=result.json())
    return result
