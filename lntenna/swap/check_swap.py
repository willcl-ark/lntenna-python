import submarine_api

import lntenna.database as db
from lntenna.server.config import CONFIG
from lntenna.swap.utilities import try_json


@try_json
def check_swap(uuid: str):
    # lookup swap details here
    network, invoice, redeem_script = db.query_swap_details(uuid)
    if network == "mainnet":
        network = "bitcoin"
    result = submarine_api.check_status(
        url=CONFIG["swap"]["URL"],
        network=network,
        invoice=invoice,
        redeem_script=redeem_script,
    )
    return result
