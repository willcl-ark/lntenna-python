from lntenna.swap import create_order, get_invoice_details, get_swap_quote


def auto_swap(request):
    """Takes a dict as argument of the following structure, with arguments 'm' for
    message, 'a' for refund address and 'n' for network:

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
    blocksat_order = create_order(message=message, bid="10000", network=network)

    # lookup the invoice with the swap server to ensure it's valid & payable
    invoice_lookup = get_invoice_details(
        invoice=blocksat_order["response"]["lightning_invoice"]["payreq"],
        network="testnet",
    )

    # get a swap quote from the swap server
    swap = get_swap_quote(
        uuid=blocksat_order["uuid"],
        invoice=blocksat_order["response"]["lightning_invoice"]["payreq"],
        network=network,
        refund_addr=refund_addr,
    )

    result = {
        "uuid": blocksat_order["uuid"],
        "inv": blocksat_order["response"]["lightning_invoice"]["payreq"],
        "amt": swap["response"]["swap_amount"],
        "addr": swap["response"]["swap_p2sh_address"],
        "r_s": swap["response"]["redeem_script"],
    }

    return result
