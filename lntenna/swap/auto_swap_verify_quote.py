import logging
from binascii import hexlify
from pprint import pformat, pprint

from lntenna.bitcoin import AuthServiceProxy, SATOSHIS
from lntenna.database import add_verify_quote
from lntenna.gotenna.utilities import log
from lntenna.lightning.lnaddr import lndecode
from lntenna.server.config import CONFIG
from lntenna.swap.decode_redeemscript import compare_redeemscript_invoice

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=CONFIG["logging"]["FORMAT"])


def proxy():
    """Return a fresh proxy instance for each call
    """
    return AuthServiceProxy()


def auto_swap_verify_quote(message, cli=False):
    result = {}
    if cli:
        print("\n---------------------------------------\n\n")
        log(f"Your lntenna UUID for this order is: {message['uuid']}", cli)
        print(f"You can use this to re-send swap_tx message to GATEWAY and to query "
              f"status of interrupted swaps.")
        print("\n\n---------------------------------------\n")
    # decode the invoice, raise value error if signature mismatch
    decoded_inv = lndecode(message["inv"])
    log({"Decoded invoice": decoded_inv}, cli)
    log({"Redeem script": message["r_s"]}, cli)

    # Check the Pubkey from the invoice matches hardcoded keys
    log("Checking decoded pubkey matches known blockstream pubkeys...", cli)
    pubkey = hexlify(decoded_inv.pubkey.serialize()).decode("utf-8")
    assert pubkey in CONFIG["blocksat_pubkeys"].values()
    log(f"Pubkey {pubkey} successfully matched to hardcoded keys in config.ini!", cli)

    # check the redeem_script matches the lightning invoice payment_hash
    log("Checking swap redeem script matches lightning invoice payment hash...", cli)
    payment_hash = decoded_inv.paymenthash.hex()
    assert compare_redeemscript_invoice(payment_hash, message["r_s"])
    log("Redeem script and payment hash match", cli)

    # calculate amount the bitcoin transaction
    amount = f'{message["amt"] / SATOSHIS:.8f}'
    if cli:
        print(f"\nAre you happy to proceed with creating bitcoin transaction for "
              f"{amount} Bitcoin to fulfill swap request\n")
        res = input("Enter 'y' to continue\t")
        if res.lower() != 'y':
            print("satellite message payment cancelled")
            return

    # setup the transaction
    result["tx_hash"] = proxy().sendtoaddress(message["addr"], amount)
    tx_hash = proxy().gettransaction(result["tx_hash"])
    result["tx_hex"] = tx_hash["hex"]
    # TODO: for separate machines should change to getrawtransaction as per below
    # result["tx_hex"] = proxy.getrawtransaction(result["tx_hash"])
    result["uuid"] = message["uuid"]

    # write to db as we don't have it on our side yet.:
    add_verify_quote(
        message["uuid"],
        message["inv"],
        message["amt"],
        message["addr"],
        message["r_s"],
        pubkey,
        payment_hash,
        tx_hash["txid"],
        tx_hash["hex"],
    )

    log(f"Returning swap tx to GATEWAY:\n{pformat(result)}", cli)
    return {"swap_tx": result}
