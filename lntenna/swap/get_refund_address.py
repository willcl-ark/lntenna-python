from lntenna.database import db
from lntenna.server.config import connection


def get_refund_address(uuid: str, addr_type: str):
    result = connection.btc_proxy.getnewaddress("", addr_type)
    status_code = 200
    try:
        db.add_refund_addr(uuid=uuid, refund_addr=result)
    except Exception as e:
        result = {"result": result, "error": e}
        status_code = 400
    return {"result": result, "status_code": status_code}
