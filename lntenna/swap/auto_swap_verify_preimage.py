import hashlib
import logging

from lntenna.bitcoin import AuthServiceProxy
from lntenna.database import swap_add_preimage
from lntenna.gotenna.utilities import log
from lntenna.server.config import CONFIG

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=CONFIG["logging"]["FORMAT"])

proxy = AuthServiceProxy()


def auto_swap_verify_preimage(uuid, preimage: str, payment_hash: str, cli):
    preimage_hash = hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
    assert preimage_hash == payment_hash
    swap_add_preimage(uuid, preimage)
    log(
        f"Hashing preimage to check for match...\n"
        f"Returned preimage: {preimage}\nhashes to preimage hash: {preimage_hash}\n"
        f"Preimage satisfies payment hash!",
        cli,
    )

    return True
