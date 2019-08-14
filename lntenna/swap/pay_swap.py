from lntenna.server.config import SATOSHIS
from lntenna.server.bitcoind_password import BITCOIND_PW
from lntenna.database import db
from lntenna.server.config import connection


def pay_swap(uuid: str):
    swap_amount, swap_p2sh_address = db.lookup_pay_details(uuid)
    swap_amount_bitcoin = swap_amount / SATOSHIS

    # unlock the wallet if locked
    network = db.lookup_network(uuid)
    try:
        txid = connection.btc_proxy.sendtoaddress(
            swap_p2sh_address, swap_amount_bitcoin
        )
    except Exception:
        connection.btc_proxy.walletpassphrase(BITCOIND_PW, 60)
        txid = connection.btc_proxy.sendtoaddress(
            swap_p2sh_address, swap_amount_bitcoin
        )
        connection.btc_proxy.walletlock()

    # add the txid to the db
    try:
        db.add_txid(uuid=uuid, txid=txid)
        response = {"txid": txid, "status_code": 200}
    except Exception as e:
        response = {"error": e, "status_code": 400}
    return response
