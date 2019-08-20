import lntenna.database as db
from lntenna.bitcoin.authproxy import AuthServiceProxy
from lntenna.swap.utilities import try_json


@try_json
def get_refund_address(uuid: str, addr_type: str):
    btc = AuthServiceProxy()
    result = btc.getnewaddress("", addr_type)
    # TODO: check the workflow of this being removed
    # try:
    #     db.add_refund_addr(uuid=uuid, refund_addr=result)
    # except Exception as e:
    #     raise e
    return result
