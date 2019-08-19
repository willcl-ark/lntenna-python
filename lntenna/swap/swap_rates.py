import submarine_api
from lntenna.server.config import CONFIG
from lntenna.swap.utilities import try_json


@try_json
def swap_rates():
    return submarine_api.get_exchange_rates(url=CONFIG["swap"]["URL"])
