import logging
from pprint import pformat

from lntenna.server.config import FORMAT
from lntenna.swap.create_order import create_order
from lntenna.swap.get_invoice_details import get_invoice_details
from lntenna.swap.get_swap_quote import get_swap_quote

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=FORMAT)


def auto_swap_create(request):
    """Takes a dict as argument of the following structure, with arguments
    "m" - message,
    "a" - refund address
    "n" - network:

    {"sat_req":
        {"m": "Hello, World!",
         "a": "mut6HiwhKab6csGyUBbacoHDq7BvENVti8",
         "n": "t"
         }
    }

    """
    # parse request
    message = request["m"]
    refund_addr = request["a"]
    network = "testnet" if request["n"] is "t" else "mainnet"

    # create blocksat order
    # TODO: Add some bid creation logic here or somewhere else...
    blocksat_order = create_order(message=message, bid="10000", network=network)

    # lookup the invoice with the swap server to ensure it's valid & payable
    assert (
        get_invoice_details(
            invoice=blocksat_order["response"]["lightning_invoice"]["payreq"],
            network="testnet",
        )
        is not None
    )

    # get a swap quote from the swap server
    swap = get_swap_quote(
        uuid=blocksat_order["uuid"],
        invoice=blocksat_order["response"]["lightning_invoice"]["payreq"],
        network=network,
        refund_addr=refund_addr,
    )

    result = {
        "sat_fill": {
            "uuid": blocksat_order["uuid"],
            "inv": blocksat_order["response"]["lightning_invoice"]["payreq"],
            "amt": swap["response"]["swap_amount"],
            "addr": swap["response"]["swap_p2sh_address"],
            "r_s": swap["response"]["redeem_script"],
        }
    }

    logger.debug(f"Auto_swap result: {pformat(result)}")

    return result
