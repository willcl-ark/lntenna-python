import submarine_api
from lntenna.server.config import SUBMARINE_API


def swap_rates():
    result = submarine_api.get_exchange_rates(url=SUBMARINE_API)
    return {"result": result.text,
            "status_code": result.status_code}
