from lntenna.server.config import CONFIG
import submarine_api
from lntenna.swap.utilities import try_json


@try_json
def get_address_details(address, network):
    return submarine_api.get_address_details(
        CONFIG["swap"]["URL"], address, network
    )
