import logging
import time
from pprint import pformat

from submarine_api import broadcast_tx

import lntenna.database as db
from lntenna.bitcoin import AuthServiceProxy, make_service_url
from lntenna.gotenna.utilities import log
from lntenna.server.config import CONFIG
from lntenna.swap.check_swap import check_swap

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=CONFIG["logging"]["FORMAT"])


def broadcast_transaction(uuid, tx_hex, cli):
    network = db.orders_get_network(uuid)
    proxy = AuthServiceProxy(service_url=make_service_url(network))
    log(f"Broadcasting transaction", cli)
    try:
        proxy.getbalance()
        bitcoind = True
    except ConnectionRefusedError:
        bitcoind = False

    if bitcoind:
        log("Bitcoind active", cli)
        tx_hash = proxy.sendrawtransaction(tx_hex)
        log(f"Transaction submitted via bitcoind:\n{pformat(tx_hash)}", cli)
    else:
        log("Uploading transaction using submarine_api...", cli)
        tx_hash = broadcast_tx(CONFIG["swap"]["URL"], network, tx_hex)
        log(f"Transaction submitted via submarine_api:\n{pformat(tx_hash)}", cli)

    return tx_hash


def monitor_swap_status(uuid, cli, interval, timeout, conn=None):
    conn.log(
        f"Starting swap status monitor for {timeout} seconds with an interval "
        f"of {interval} seconds."
    )
    start = time.time()
    swap_status = None
    tries = 0

    while True and time.time() < start + timeout:
        swap_status = check_swap(uuid)
        tries += 1
        if conn:
            conn.log(f"Swap status try {tries}:\n{pformat(swap_status)}")
        if "payment_secret" in swap_status["response"]:
            conn.log(
                f"Payment secret detected:\n"
                f"{swap_status['response']['payment_secret']}"
            )
            db.swaps_add_preimage(uuid, swap_status["response"]["payment_secret"])
            return swap_status
        time.sleep(interval)
    conn.log("Swap status monitor ending")
    return swap_status


def auto_swap_complete(uuid, tx_hex, cli, conn):
    network = db.orders_get_network(uuid)
    result = {"uuid": uuid}
    # broadcast the tx
    result["tx_hash"] = broadcast_transaction(uuid, tx_hex, cli)
    # monitor the swap status to see when the swap has been fulfilled
    if network == "mainnet":
        # if mainnet use longer interval and timeout as SSS needs 1 confirmation
        swap_status = monitor_swap_status(
            uuid, cli, interval=30, timeout=720, conn=conn
        )
    else:
        # if testnet, monitor at quicker interval and lower timeout
        swap_status = monitor_swap_status(uuid, cli, interval=5, timeout=300, conn=conn)
    if "payment_secret" in swap_status["response"]:
        conn.log(f"Swap complete!:\n{pformat(swap_status['response'])}")
        result["payment_secret"] = swap_status["response"]["payment_secret"]
    else:
        conn.log(f"Swap not yet complete:\n{pformat(swap_status['response'])}")
        result["status"] = "incomplete"
        result["details"] = swap_status["response"]
    return {"swap_status": result}
