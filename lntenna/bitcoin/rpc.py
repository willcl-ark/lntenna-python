import bitcoin
import bitcoin.core
import bitcoin.rpc

from lntenna.server.config import BTC_CONF_PATH, BTC_NETWORK

SATOSHIS = 100_000_000
networks = ["mainnet", "testnet", "regtest"]


class BitcoinProxy:
    def __init__(self, btc_conf_file=BTC_CONF_PATH, network=BTC_NETWORK):
        self.btc_conf_file = btc_conf_file
        self._btc_network = network
        bitcoin.SelectParams(self._btc_network)

    @property
    def network(self):
        return self._btc_network

    @network.setter
    def network(self, network):
        """
        :param network: one of "mainnet", "testnet" or "regtest"
        """
        assert network in networks
        self._btc_network = network
        bitcoin.SelectParams(self.network)

    @property
    def raw_proxy(self):
        return bitcoin.rpc.RawProxy(btc_conf_file=self.btc_conf_file)

    @property
    def proxy(self):
        return bitcoin.rpc.Proxy(btc_conf_file=self.btc_conf_file)

    def send_last_tx(self):
        """Try to broadcast the last tx in the wallet in case of errors during swap
        """
        last_txid = self.raw_proxy.listtransactions()[-1]["txid"]
        tx_hex = self.raw_proxy.gettransaction(last_txid)['hex']
        self.raw_proxy.sendrawtransaction(tx_hex)
