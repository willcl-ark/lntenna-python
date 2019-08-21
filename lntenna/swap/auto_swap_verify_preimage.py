import hashlib
import logging

from lntenna.database import swap_add_preimage
from lntenna.gotenna.utilities import log
from lntenna.server.config import CONFIG

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=CONFIG["logging"]["FORMAT"])


def auto_swap_verify_preimage(uuid, preimage: str, payment_hash: str, cli):
    preimage_hash = hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
    assert preimage_hash == payment_hash
    swap_add_preimage(uuid, preimage)
    log(
        f"Hashing preimage to check for match...\n"
        f"Returned preimage: {preimage}\nhashes to preimage hash: {preimage_hash}\n"
        f"Preimage satisfies payment hash!\n"
        f"Swap complete -- lightning invoice satisfied. Watch Blocksat feed for "
        f"message.",
        cli,
    )

    return True
