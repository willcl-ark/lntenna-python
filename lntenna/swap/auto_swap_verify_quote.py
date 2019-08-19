import logging
from binascii import hexlify
from pprint import pformat

from lntenna.bitcoin import BitcoinProxy, SATOSHIS
from lntenna.database import add_verify_quote
from lntenna.lightning.lnaddr import lndecode
from lntenna.server.config import BLOCKSAT_NODE_PUBKEYS, FORMAT
from lntenna.swap.decode_redeemscript import compare_redeemscript_invoice

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=FORMAT)


def proxy():
    """Return a fresh proxy instance for each call
    """
    return BitcoinProxy().raw_proxy


def auto_swap_verify_quote(message):
    result = {}
    # decode the invoice, raise value error if signature mismatch
    decoded_inv = lndecode(message["inv"])
    logger.debug(f"Decoded invoice: {decoded_inv}")

    # Check the Pubkey from the invoice matches hardcoded keys
    logger.debug("Check decoded pubkey matches known blockstream pubkeys")
    pubkey = hexlify(decoded_inv.pubkey.serialize()).decode("utf-8")
    assert pubkey in BLOCKSAT_NODE_PUBKEYS
    logger.debug(f"Pubkey {pubkey} successfully matched in hardcoded keys")

    # check the redeem_script matches the lightning invoice payment_hash
    logger.debug("Checking swap redeem script matches lightning invoice payment hash")
    payment_hash = decoded_inv.paymenthash.hex()
    assert compare_redeemscript_invoice(payment_hash, message["r_s"])
    logger.debug("Redeem script and lightning invoice match")

    # create the bitcoin transaction
    amount = f'{message["amt"] / SATOSHIS:.8f}'
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

    logger.debug(f"Returning result from auto_swap_verify_quote(): {pformat(result)}")
    return {"swap_tx": result}
