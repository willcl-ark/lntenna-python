import logging
import time
from pprint import pformat

from submarine_api import broadcast_tx

import lntenna.database as db
from lntenna.bitcoin import AuthServiceProxy
from lntenna.gotenna.utilities import log
from lntenna.server.config import CONFIG
from lntenna.swap.check_swap import check_swap

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=CONFIG["logging"]["FORMAT"])

proxy = AuthServiceProxy()


def broadcast_transaction(uuid, tx_hex, cli):
    network = db.lookup_network(uuid)
    log(f"Broadcasting transaction", cli)
    try:
        proxy.getbalance()
        bitcoind = True
    except ConnectionRefusedError:
        bitcoind = False

    if bitcoind:
        log("Bitcoind active", cli)
        tx_hash = proxy.sendrawtransaction(tx_hex)
        log(f"Transaction submitted via bitcoind:\n{tx_hash}", cli)
    else:
        log("Uploading transaction using submarine_api...", cli)
        tx_hash = broadcast_tx(CONFIG["swap"]["URL"], network, tx_hex)
        log(f"Transaction submitted via submarine_api:\n{tx_hash}", cli)

    return tx_hash


def monitor_swap_status(uuid, cli):
    log("Starting swap status monitor", cli)

    while True:
        swap_status = check_swap(uuid)
        if "response" in swap_status:
            if "payment_secret" in swap_status["response"]:
                log(
                    f"Payment secret detected:\n"
                    f"{swap_status['response']['payment_secret']}",
                    cli,
                )
                return swap_status["response"]["payment_secret"]
        time.sleep(5)


def auto_swap_complete(uuid, tx_hex, cli):
    result = {"uuid": uuid}
    # broadcast the tx
    result["tx_hash"] = broadcast_transaction(uuid, tx_hex, cli)
    # monitor the swap status to see when the swap has been fulfilled
    result["preimage"] = monitor_swap_status(uuid, cli)
    log(f"auto_swap_complete result:\n{pformat(result)}", cli)
    return {"swap_complete": result}
