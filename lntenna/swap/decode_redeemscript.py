import hashlib

from lntenna.bitcoin import AuthServiceProxy

proxy = AuthServiceProxy()


def compare_redeemscript_invoice(payment_hash: str, redeem_script: str):
    # decode bitcoin script
    decoded_script = proxy.decodescript(redeem_script)
    decoded_list = decoded_script["asm"].split(" ")
    script_hash = decoded_list[2]

    # get the RIPEMD160 hash of the payment_hash
    ph_bytes = bytes.fromhex(payment_hash)
    ph_ripemd160 = hashlib.new("ripemd160", ph_bytes).hexdigest()

    if ph_ripemd160 == script_hash:
        return True
    return False
