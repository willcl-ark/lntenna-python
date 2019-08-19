import hashlib
import logging

from lntenna.bitcoin import BitcoinProxy
from lntenna.database import swap_add_preimage
from lntenna.server.config import CONFIG

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=CONFIG["logging"]["FORMAT"])

proxy = BitcoinProxy().raw_proxy


def auto_swap_verify_preimage(uuid, preimage: str, payment_hash: str):
    preimage_hash = hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
    assert preimage_hash == payment_hash
    swap_add_preimage(uuid, preimage)
    print(
        f"Successfully hashed preimage to match payment hash.\n"
        f"Preimage:\n{preimage}\nhashes to preimage hash:\n{preimage_hash}\n"
        f"which matches payment hash:\n{payment_hash}"
    )

    return True
