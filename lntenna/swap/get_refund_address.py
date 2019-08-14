from lntenna.database import db
from lntenna.bitcoin.rpc import BitcoinProxy


def get_refund_address(uuid: str, addr_type: str):
    btc = BitcoinProxy()
    result = btc.raw_proxy.getnewaddress("", addr_type)
    try:
        db.add_refund_addr(uuid=uuid, refund_addr=result)
    except Exception as e:
        result = {"result": result, "database_error": e}
    return result
