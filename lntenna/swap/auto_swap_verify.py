import logging

from lntenna.lightning.lnaddr import lndecode
from lntenna.server.config import BLOCKSAT_NODE_PUBKEYS, SATOSHIS
from lntenna.swap.decode_redeemscript import compare_redeemscript_invoice
from binascii import hexlify


logger = logging.getLogger(__name__)
FORMAT = "[%(levelname)s - %(funcname)s] - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)


def auto_swap_verify(message, btc_proxy):
    result = {}
    # attempt decode, raise value error if signature mismatch
    decoded_inv = lndecode(message["inv"])
    logger.debug(f"Decoded invoice: {decoded_inv}")

    # Check the Pubkey from the lninvoice matches pre-known keys
    # This key might be supplied with invoice, or derived from signature, it doesn't matter.

    assert (
        hexlify(decoded_inv.pubkey.serialize()).decode("utf-8") in BLOCKSAT_NODE_PUBKEYS
    )

    # check the redeem_script matches the lightning invoice payment_hash
    assert compare_redeemscript_invoice(decoded_inv.paymenthash.hex(), message["r_s"])

    # create the bitcoin transaction
    amount = f'{message["amt"] / SATOSHIS:.8f}'
    result["tx_hash"] = btc_proxy.sendtoaddress(message["addr"], amount)
    tx = btc_proxy.gettransaction(result["tx_hash"])
    result["tx_hex"] = tx["hex"]
    # TODO: for separate machines should change to getrawtransaction as per below
    # result["tx_hex"] = btc_proxy.getrawtransaction(result["tx_hash"])
    result["uuid"] = message["uuid"]
    logger.debug(f"Returning result from auto_swap_verify(): {result}")
    return {"swap_tx": result}
