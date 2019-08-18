import logging
from binascii import hexlify
from pprint import pformat

from lntenna.bitcoin.rpc import BitcoinProxy, SATOSHIS
from lntenna.lightning.lnaddr import lndecode
from lntenna.server.config import BLOCKSAT_NODE_PUBKEYS, FORMAT
from lntenna.swap.decode_redeemscript import compare_redeemscript_invoice

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

proxy = BitcoinProxy().raw_proxy


def auto_swap_verify(message):
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
    assert compare_redeemscript_invoice(decoded_inv.paymenthash.hex(), message["r_s"])
    logger.debug("Redeem script and lightning invoice match")

    # create the bitcoin transaction
    amount = f'{message["amt"] / SATOSHIS:.8f}'
    result["tx_hash"] = proxy.sendtoaddress(message["addr"], amount)
    tx = proxy.gettransaction(result["tx_hash"])
    result["tx_hex"] = tx["hex"]
    # TODO: for separate machines should change to getrawtransaction as per below
    # result["tx_hex"] = proxy.getrawtransaction(result["tx_hash"])
    result["uuid"] = message["uuid"]
    logger.debug(f"Returning result from auto_swap_verify(): {pformat(result)}")
    return {"swap_tx": result}
