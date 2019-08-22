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
    swap_amount, swap_p2sh_address = db.swaps_get_pay_details(uuid)
    swap_amount_bitcoin = swap_amount / SATOSHIS

    # try to pay using sendtoaddress
    try:
        txid = proxy.sendtoaddress(swap_p2sh_address, swap_amount_bitcoin)
    except Exception:
        # if exception raised, try using BITCOIND_PW to unlock the wallet
        try:
            proxy.walletpassphrase(BITCOIND_PW, 60)
            txid = proxy.sendtoaddress(swap_p2sh_address, swap_amount_bitcoin)
            proxy.walletlock()
        except Exception as e:
            # if still failing, return the error
            response = {"error": e, "status_code": 400}
            return response

    # add the txid to the db
    try:
        db.orders_add_txid(uuid=uuid, txid=txid)
        return {"txid": txid, "status_code": 200}
    except Exception as e:
        return {"error": e, "status_code": 400}
