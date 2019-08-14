from lntenna.server.config import SUBMARINE_API
import submarine_api


def get_address_details(invoice, network):
    return submarine_api.get_address_details(SUBMARINE_API, invoice, network).json()
