import binascii

from lntenna.bitcoin import AuthServiceProxy, OP_RIPEMD160

proxy = AuthServiceProxy()


def verify_redeem_script(
    payment_hash: str, redeem_script: str, swap_address: str, refund_addr: str
):
    # decode bitcoin script
    decoded_script = proxy.decodescript(redeem_script)
    decoded_list = decoded_script["asm"].split(" ")

    # decode the refund address
    refund_addr_info = proxy.getaddressinfo(refund_addr)
    decoded_addr = proxy.decodescript(refund_addr_info["scriptPubKey"])
    decoded_addr_script = decoded_addr["asm"].split(" ")

    # get the RIPEMD160 hash of the payment_hash
    payment_hash_bytes = bytes.fromhex(payment_hash)
    payment_hash_RIPEMD160 = binascii.hexlify(OP_RIPEMD160(payment_hash_bytes)).decode(
        "utf-8"
    )

    # script assertions
    assert decoded_list[0] == "OP_DUP"
    assert decoded_list[1] == "OP_HASH160"
    assert decoded_list[2] == payment_hash_RIPEMD160
    assert decoded_list[3] == "OP_EQUAL"
    assert decoded_list[4] == "OP_IF"
    assert decoded_list[5] == "OP_DROP"
    # swap provider inserts own lightning node pubkey here
    assert decoded_list[7] == "OP_ELSE"
    # locktime here, could look up from current block time to make sure sane?
    assert decoded_list[9] == "OP_CHECKLOCKTIMEVERIFY"
    assert decoded_list[10] == "OP_DROP"
    assert decoded_list[11] == "OP_DUP"
    assert decoded_list[12] == "OP_HASH160"
    assert decoded_list[13] == decoded_addr_script[2]
    assert decoded_list[14] == "OP_EQUALVERIFY"
    assert decoded_list[15] == "OP_ENDIF"
    assert decoded_list[16] == "OP_CHECKSIG"

    # verify redeem script encodes to P2SH address provided by the swap server
    assert (
        swap_address == decoded_script["p2sh"]
        or swap_address == decoded_script["segwit"]["p2sh-segwit"]
    ) or swap_address in decoded_script["segwit"]["addresses"]
