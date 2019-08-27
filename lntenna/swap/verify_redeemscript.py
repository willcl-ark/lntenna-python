import hashlib

from lntenna.bitcoin import AuthServiceProxy

proxy = AuthServiceProxy()


def verify_redeem_script(payment_hash: str, redeem_script: str, swap_address: str):
    # decode bitcoin script
    decoded_script = proxy.decodescript(redeem_script)
    decoded_list = decoded_script["asm"].split(" ")
    script_hash = decoded_list[2]

    # get the RIPEMD160 hash of the payment_hash
    ph_bytes = bytes.fromhex(payment_hash)
    ph_ripemd160 = hashlib.new("ripemd160", ph_bytes).hexdigest()

    assert ph_ripemd160 == script_hash

    # verify redeem script encodes to P2SH address provided by the swap server
    assert (
        swap_address == decoded_script["p2sh"]
        or swap_address == decoded_script["segwit"]["addresses"][0]
        or swap_address == decoded_script["segwit"]["p2sh-segwit"]
    )
