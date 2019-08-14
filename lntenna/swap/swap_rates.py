import submarine_api


def swap_rates():
    result = submarine_api.get_exchange_rates()
    return {"result": result.text,
            "status_code": result.status_code}
