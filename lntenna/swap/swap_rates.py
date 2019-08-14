import submarine_api
from lntenna.server.config import SUBMARINE_API
from lntenna.swap.utilities import try_json


@try_json
def swap_rates():
    return submarine_api.get_exchange_rates(url=SUBMARINE_API)
