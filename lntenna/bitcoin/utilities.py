import hashlib
import base58


def OP_RIPEMD160(data: bytes):
    return hashlib.new("ripemd160", data).digest()


def OP_SHA256(data: bytes):
    return hashlib.sha256(data).digest()


def OP_HASH160(data: bytes):
    sha256 = hashlib.sha256(data).digest()
    return hashlib.new("ripemd160", sha256).digest()


def OP_HASH256(data: bytes):
    sha256 = hashlib.sha256(data).digest()
    return hashlib.sha256(sha256).digest()
