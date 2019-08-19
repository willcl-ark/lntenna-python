import logging

import submarine_api

from lntenna.server.config import CONFIG
from lntenna.swap.utilities import try_json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=CONFIG["logging"]["FORMAT"])


@try_json
def get_invoice_details(invoice: str, network: str):
    logger.debug("Getting invoice details from swap server to confirm availability")
    inv = submarine_api.get_invoice_details(
        CONFIG["swap"]["URL"], network, invoice
    )
    if inv.status_code == 200:
        logger.debug("Successfully got invoice details")
        return inv
    else:
        return False
