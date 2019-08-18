import logging
import time

from submarine_api import broadcast_tx, check_status

from lntenna.bitcoin.rpc import BitcoinProxy
from lntenna.database import db
from lntenna.server.config import SUBMARINE_API
from lntenna.swap.check_swap import check_swap


logger = logging.getLogger(__name__)
FORMAT = "[%(levelname)s - %(funcname)s] - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

bitcoin = BitcoinProxy()


def broadcast_transaction(uuid, tx_hex, bitcoin_proxy):
    network = db.lookup_network(uuid)
    logger.debug(f"BROADCAST_TRANSACTION: network = {network}")
    try:
        bitcoin_proxy.getbalance()
        bitcoind = True
    except ConnectionRefusedError:
        bitcoind = False

    if bitcoind:
        logger.debug("Bitcoind active")
        tx_hash = bitcoin_proxy.sendrawtransaction(tx_hex)
        logger.debug(f"Transaction submitted via bitcoind: {tx_hash}")
    else:
        logger.debug("Uploading transaction using submarine_api...")
        tx_hash = broadcast_tx(SUBMARINE_API, network, tx_hex)
        logger.debug(f"Transaction submitted via submarine_api: {tx_hash}")

    return tx_hash


def monitor_swap_status(uuid):
    logger.debug("Starting swap status monitor")
    network, invoice, redeem_script = db.lookup_swap_details(uuid)

    while True:
        # swap_status = connection.check_swap(uuid=uuid)
        swap_status = check_swap(uuid)
        logger.debug(f"swap_status: {swap_status}")
        if "response" in swap_status:
            if "payment_secret" in swap_status["response"]:
                logger.debug(
                    f"Payment secret detected: {swap_status['response']['payment_secret']}"
                )
                return swap_status["response"]["payment_secret"]
        time.sleep(5)


def auto_swap_complete(uuid, tx_hex, connection):
    result = {}
    # broadcast the tx
    result["tx_hash"] = broadcast_transaction(uuid, tx_hex, bitcoin.raw_proxy)
    # monitor the swap status to see when the swap has been fulfilled
    result["preimage"] = monitor_swap_status(uuid)
    logger.debug(f"auto_swap_complete result: {result}")
    return {"SWAP_COMPLETE": result}
