import logging
from binascii import hexlify
from pprint import pformat, pprint

from lntenna.bitcoin import AuthServiceProxy, SATOSHIS
from lntenna.database import add_verify_quote
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
    # decode the invoice, raise value error if signature mismatch
    decoded_inv = lndecode(message["inv"])
    pprint(f"Decoded invoice: {decoded_inv}")
    pprint(f"Redeem script: {message['r_s']}")

    # Check the Pubkey from the invoice matches hardcoded keys
    print("Check decoded pubkey matches known blockstream pubkeys")
    pubkey = hexlify(decoded_inv.pubkey.serialize()).decode("utf-8")
    assert pubkey in CONFIG["blocksat_pubkeys"].values()
    print(f"Pubkey {pubkey} successfully matched in hardcoded keys")

    # check the redeem_script matches the lightning invoice payment_hash
    print("Checking swap redeem script matches lightning invoice payment hash")
    payment_hash = decoded_inv.paymenthash.hex()
    assert compare_redeemscript_invoice(payment_hash, message["r_s"])
    print("Redeem script and lightning invoice match")

    # calculate amount the bitcoin transaction
    amount = f'{message["amt"] / SATOSHIS:.8f}'
    if cli:
        print(f"Are you happy to proceed with creating bitcoin transaction for "
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

    pprint(f"Returning result from auto_swap_verify_quote(): {pformat(result)}")
    return {"swap_tx": result}
