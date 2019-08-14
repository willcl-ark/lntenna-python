import logging

from lntenna.swap import (
    bump_blocksat_order,
    check_swap,
    create_order,
    get_address_details,
    get_invoice_details,
    get_refund_address,
    get_swap_quote,
    pay_swap,
    swap_rates,
)

logger = logging.getLogger(__name__)
FORMAT = "[%(asctime)s - %(levelname)s] - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)


def auto_swap(message):
    # create blocksat order
    blocksat_order = create_order(message=message, bid="10000", network="testnet")
    logger.debug(f"blocksat_order: {blocksat_order}")

    # lookup the invoice with the swap server to ensure it's valid & payable
    invoice_lookup = get_invoice_details(
        invoice=blocksat_order["order"]["lightning_invoice"]["payreq"],
        network="testnet",
    )
    logger.debug(f"invoice_lookup: {invoice_lookup}")

    # get a bitcoin refund address
    refund_addr = get_refund_address(uuid=blocksat_order["uuid"], addr_type="legacy")
    logger.debug(f"refund_addr: {refund_addr}")

    # get a swap quote from the swap server
    swap = get_swap_quote(
        uuid=blocksat_order["uuid"],
        invoice=blocksat_order["order"]["lightning_invoice"]["payreq"],
        network="testnet",
    )
    logger.debug(f"swap: {swap}")

    # pay the swap quote
    swap_payment = pay_swap(uuid=blocksat_order["uuid"])
    logger.debug(f"pay_swap: {swap_payment}")

    # check the swap status
    check_swap_status = check_swap(uuid=blocksat_order["uuid"])
    logger.debug(f"swap_status: {check_swap_status}")
