import logging
from binascii import hexlify
from pprint import pformat, pprint

from lntenna.bitcoin import AuthServiceProxy, SATOSHIS

try:
    from lntenna.server.bitcoind_password import BITCOIND_PW
except ModuleNotFoundError:
    pass

from lntenna.database import mesh_add_verify_quote, lookup_network
from lntenna.gotenna.utilities import log
from lntenna.lightning.lnaddr import lndecode
from lntenna.server.config import CONFIG
from lntenna.swap.decode_redeemscript import compare_redeemscript_invoice

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=CONFIG["logging"]["FORMAT"])

proxy = AuthServiceProxy()


def auto_swap_verify_quote(message, cli=False):
    result = {}
    if cli:
        log("\n---------------------------------------\n\n", cli)
        log(f"Your lntenna UUID for this order is: {message['u']}", cli)
        log(
            f"You can use this to re-send swap_tx message to GATEWAY and to query "
            f"status of interrupted swaps.",
            cli,
        )
        log("\n\n---------------------------------------\n", cli)
    # decode the invoice, raise value error if signature mismatch
    decoded_inv = lndecode(message["i"])
    log(f"Decoded invoice: {decoded_inv}", cli)
    log(f"Redeem script: {message['rs']}", cli)

    # Check the Pubkey from the invoice matches hardcoded keys
    log("Checking decoded pubkey matches known blockstream pubkeys...", cli)
    pubkey = hexlify(decoded_inv.pubkey.serialize()).decode("utf-8")
    assert pubkey in CONFIG["blocksat_pubkeys"].values()
    log(f"Pubkey {pubkey} successfully matched to hardcoded keys in config.ini!", cli)

    # check the redeem_script matches the lightning invoice payment_hash
    log("Checking swap redeem script matches lightning invoice payment hash...", cli)
    payment_hash = decoded_inv.paymenthash.hex()
    assert compare_redeemscript_invoice(payment_hash, message["rs"])
    log("Redeem script and payment hash match", cli)

    # calculate amount the bitcoin transaction
    amount = f'{message["am"] / SATOSHIS:.8f}'
    if cli:
        # lookup network using UUID from db
        network = lookup_network(message["u"])
        log(
            f"\nAre you happy to proceed with creating the below transaction to fulfill"
            f" swap request:\n"
            f"\tNETWORK: {network}\n"
            f"\tAMOUNT: {amount}\n",
            cli,
        )
        res = input("Enter 'y' to continue\t") or "y"
        if res.lower() != "y":
            log("satellite message payment cancelled", cli)
            return

    # setup the transaction
    try:
        result["tx_hash"] = proxy.sendtoaddress(message["ad"], amount)
    except Exception:
        if BITCOIND_PW:
            proxy.walletpassphrase(BITCOIND_PW, 60)
            result["tx_hash"] = proxy.sendtoaddress(message["ad"], amount)
            proxy.walletlock()

    tx_hash = proxy.gettransaction(result["tx_hash"])
    result["tx_hex"] = tx_hash["hex"]
    # TODO: for separate machines should change to getrawtransaction as per below
    # result["tx_hex"] = proxy.getrawtransaction(result["tx_hash"])
    result["uuid"] = message["u"]

    # write to db as we don't have it on our side yet.:
    mesh_add_verify_quote(
        message["u"],
        message["i"],
        message["am"],
        message["ad"],
        message["rs"],
        pubkey,
        payment_hash,
        tx_hash["txid"],
        tx_hash["hex"],
    )

    log(f"Returning swap tx to GATEWAY:\n{pformat(result)}", cli)
    return {"swap_tx": result}
