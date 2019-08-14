from lntenna.server.config import SUBMARINE_API
import submarine_api


def get_invoice_details(invoice, network):
    return submarine_api.get_invoice_details(invoice, network).json()
