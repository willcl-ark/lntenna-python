import submarine_api

import lntenna.database as db
from lntenna.server.config import CONFIG
from lntenna.swap.utilities import try_json


@try_json
def get_swap_quote(uuid: str, invoice: str, network: str, refund_addr: str):
    result = submarine_api.get_quote(
        url=CONFIG["swap"]["URL"], network=network, invoice=invoice, refund=refund_addr
    )
    # add the swap to the swap table
    db.swaps_add_swap_quote(uuid=uuid, result=result.json())
    return result
