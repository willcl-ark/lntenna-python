import binascii

from lntenna.bitcoin import AuthServiceProxy, OP_RIPEMD160

proxy = AuthServiceProxy()


class ScriptAssertionError(Exception):
    pass


def verify_redeem_script(
    payment_hash: str, redeem_script: str, swap_address: str, refund_addr: str
):
    # decode bitcoin script
    decoded_script = proxy.decodescript(redeem_script)
    decoded_list = decoded_script["asm"].split(" ")

    # decode the refund address
    refund_addr_info = proxy.getaddressinfo(refund_addr)
    decoded_addr = proxy.decodescript(refund_addr_info["scriptPubKey"])
    decoded_addr_list = decoded_addr["asm"].split(" ")

    # get the RIPEMD160 hash of the payment_hash
    payment_hash_bytes = bytes.fromhex(payment_hash)
    payment_hash_RIPEMD160 = binascii.hexlify(OP_RIPEMD160(payment_hash_bytes)).decode(
        "utf-8"
    )

    # script tests according to the PKHash script from
    # https://github.com/submarineswaps/swaps-service/blob/master/docs/chain_swap_script.md#pkhash-case
    if not decoded_list[0] == "OP_DUP":
        raise ScriptAssertionError
    if not decoded_list[1] == "OP_HASH160":
        raise ScriptAssertionError
    if not decoded_list[2] == payment_hash_RIPEMD160:
        raise ScriptAssertionError("Redeem script payment hash mismatch vs invoice")
    if not decoded_list[3] == "OP_EQUAL":
        raise ScriptAssertionError
    if not decoded_list[4] == "OP_IF":
        raise ScriptAssertionError
    if not decoded_list[5] == "OP_DROP":
        raise ScriptAssertionError

    # swap provider inserts own lightning node pubkey here

    if not decoded_list[7] == "OP_ELSE":
        raise ScriptAssertionError

    # locktime here, could look up from current block time to make sure sane?

    if not decoded_list[9] == "OP_CHECKLOCKTIMEVERIFY":
        raise ScriptAssertionError
    if not decoded_list[10] == "OP_DROP":
        raise ScriptAssertionError
    if not decoded_list[11] == "OP_DUP":
        raise ScriptAssertionError
    if not decoded_list[12] == "OP_HASH160":
        raise ScriptAssertionError
    # TODO: this index varies between address formats, 2 for P2PHK and 1 for bech32?
    #   hardcoding for bech32 currently
    if not decoded_list[13] == decoded_addr_list[1]:
        raise ScriptAssertionError("Redeem script decoded address mismatch vs database")
    if not decoded_list[14] == "OP_EQUALVERIFY":
        raise ScriptAssertionError
    if not decoded_list[15] == "OP_ENDIF":
        raise ScriptAssertionError
    if not decoded_list[16] == "OP_CHECKSIG":
        raise ScriptAssertionError

    # verify redeem script encodes to P2SH address provided by the swap server
    # hardcode to P2SH-segwit

    if decoded_addr["type"] == 'witness_v0_keyhash':
        if not swap_address == decoded_script["segwit"]["p2sh-segwit"]:
            raise ScriptAssertionError
    else:
        if not swap_address == decoded_script["p2sh"]:
            raise ScriptAssertionError

    return True
