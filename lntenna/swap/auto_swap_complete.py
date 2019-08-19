import logging
import time
from pprint import pformat

from submarine_api import broadcast_tx

import lntenna.database as db
from lntenna.bitcoin import BitcoinProxy
from lntenna.server.config import CONFIG
from lntenna.swap.check_swap import check_swap

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=CONFIG["logging"]["FORMAT"])

proxy = BitcoinProxy().raw_proxy


def broadcast_transaction(uuid, tx_hex):
    network = db.lookup_network(uuid)
    logger.debug(f"Broadcasting transaction")
    try:
        proxy.getbalance()
        bitcoind = True
    except ConnectionRefusedError:
        bitcoind = False

    if bitcoind:
        logger.debug("Bitcoind active")
        tx_hash = proxy.sendrawtransaction(tx_hex)
        logger.debug(f"Transaction submitted via bitcoind: {tx_hash}")
    else:
        logger.debug("Uploading transaction using submarine_api...")
        tx_hash = broadcast_tx(CONFIG["swap"]["URL"], network, tx_hex)
        logger.debug(f"Transaction submitted via submarine_api: {tx_hash}")

    return tx_hash


def monitor_swap_status(uuid):
    logger.debug("Starting swap status monitor")

    while True:
        swap_status = check_swap(uuid)
        if "response" in swap_status:
            if "payment_secret" in swap_status["response"]:
                logger.debug(
                    f"Payment secret detected: {swap_status['response']['payment_secret']}"
                )
                return swap_status["response"]["payment_secret"]
        time.sleep(5)


def auto_swap_complete(uuid, tx_hex):
    result = {"uuid": uuid}
    # broadcast the tx
    result["tx_hash"] = broadcast_transaction(uuid, tx_hex)
    # monitor the swap status to see when the swap has been fulfilled
    result["preimage"] = monitor_swap_status(uuid)
    logger.debug(f"auto_swap_complete result: {pformat(result)}")
    return {"swap_complete": result}
