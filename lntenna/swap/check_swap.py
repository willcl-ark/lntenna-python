import lntenna.database as db
from lntenna.server.config import CONFIG
from lntenna.swap.utilities import try_json
import submarine_api


@try_json
def check_swap(uuid: str):
    # lookup swap details here
    network, invoice, redeem_script = db.lookup_swap_details(uuid)
    result = submarine_api.check_status(
        url=CONFIG["swap"]["URL"],
        network=network,
        invoice=invoice,
        redeem_script=redeem_script,
    )
    return result
