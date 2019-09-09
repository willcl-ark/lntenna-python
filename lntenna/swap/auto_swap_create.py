import logging
from pprint import pformat

from lntenna.gotenna.utilities import log
from lntenna.server.config import CONFIG
from lntenna.swap.create_blocksat_order import create_blocksat_order
from lntenna.swap.get_invoice_details import get_invoice_details
from lntenna.swap.get_swap_quote import get_swap_quote

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=CONFIG["logging"]["FORMAT"])


def auto_swap_create(request, cli):
    """Takes a dict as argument of the following structure, with arguments
    "m" - message,
    "a" - refund address
    "n" - network
    "u" - shared uuid (8 chars from uuid4)

    {"sat_req":
        {"m": "Hello, World!",
         "a": "mut6HiwhKab6csGyUBbacoHDq7BvENVti8",
         "n": "t"
         "u": "721cbf09"
         }
    }

    """
    # parse request
    message = request["m"]
    refund_addr = request["a"]
    blocksat_network = "testnet" if request["n"] == "t" else "mainnet"
    submarine_network = "testnet" if request["n"] == "t" else "bitcoin"
    uuid = request["u"]

    # create blocksat order
    # TODO: Add some bid creation logic here or somewhere else...
    blocksat_order = create_blocksat_order(
        message=message, bid="10000", network=blocksat_network, uuid=uuid
    )

    # lookup the invoice with the swap server to ensure it's valid & payable
    assert (
        get_invoice_details(
            invoice=blocksat_order["response"]["lightning_invoice"]["payreq"],
            network=submarine_network,
        )
        is not None
    )

    # get a swap quote from the swap server
    swap = get_swap_quote(
        uuid=uuid,
        invoice=blocksat_order["response"]["lightning_invoice"]["payreq"],
        network=submarine_network,
        refund_addr=refund_addr,
    )

    result = {
        "sat_fill": {
            "u": uuid,
            "i": blocksat_order["response"]["lightning_invoice"]["payreq"],
            "am": swap["response"]["swap_amount"],
            "ad": swap["response"]["swap_p2wsh_address"],
            "rs": swap["response"]["redeem_script"],
        }
    }

    log(f"Auto_swap result: \n{pformat(result)}", cli)

    return result
