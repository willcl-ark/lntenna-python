import submarine_api
from lntenna.server.config import SUBMARINE_API_URL
from lntenna.swap import try_json


@try_json
def swap_rates():
    return submarine_api.get_exchange_rates(url=SUBMARINE_API_URL)
