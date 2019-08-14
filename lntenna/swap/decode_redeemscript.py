import hashlib
from lntenna.bitcoin.rpc import BitcoinProxy
# from lntenna.swap.utilities import try_json


# @try_json
def compare_redeemscript_invoice(inv_pubkey: str, redeem_script: str):
    # decode bitcoin script
    btc = BitcoinProxy()
    decoded_script = btc.raw_proxy.decodescript(redeem_script)
    decoded_list = decoded_script["asm"].split(" ")

    # get the OP_HASH160 of the ln_invoice_pubkey
    pubkey_bytes = inv_pubkey.encode()
    sha256_hash = hashlib.sha256(pubkey_bytes).digest()
    ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()
    result = ripemd160_hash.hex()
    print(result)


