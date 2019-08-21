import lntenna.database as db
from lntenna.bitcoin import AuthServiceProxy, SATOSHIS

try:
    from lntenna.server.bitcoind_password import BITCOIND_PW
except ModuleNotFoundError:
    pass
from lntenna.swap.utilities import try_json


@try_json
def pay_swap(uuid: str):
    proxy = AuthServiceProxy()
    swap_amount, swap_p2sh_address = db.lookup_pay_details(uuid)
    swap_amount_bitcoin = swap_amount / SATOSHIS

    # unlock the wallet if locked
    network = db.lookup_network(uuid)
    try:
        txid = proxy.sendtoaddress(swap_p2sh_address, swap_amount_bitcoin)
    except Exception:
        if BITCOIND_PW:
            proxy.walletpassphrase(BITCOIND_PW, 60)
            txid = proxy.sendtoaddress(swap_p2sh_address, swap_amount_bitcoin)
            proxy.walletlock()

    # add the txid to the db
    try:
        db.add_txid(uuid=uuid, txid=txid)
        response = {"txid": txid, "status_code": 200}
    except Exception as e:
        response = {"error": e, "status_code": 400}
    return response
