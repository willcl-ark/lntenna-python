from lntenna.server.config import SUBMARINE_API
import submarine_api


def get_invoice_details(invoice: str, network: str):
    return submarine_api.get_invoice_details(SUBMARINE_API, network, invoice)
