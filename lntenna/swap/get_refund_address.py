from lntenna.database import db
from lntenna.bitcoin.rpc import BitcoinProxy
from lntenna.swap.utilities import try_json


@try_json
def get_refund_address(uuid: str, addr_type: str):
    btc = BitcoinProxy()
    result = btc.raw_proxy.getnewaddress("", addr_type)
    try:
        db.add_refund_addr(uuid=uuid, refund_addr=result)
    except Exception as e:
        raise e
    return result
