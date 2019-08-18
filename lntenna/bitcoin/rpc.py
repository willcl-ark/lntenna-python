import bitcoin
import bitcoin.core
import bitcoin.rpc

from lntenna.server.config import BTC_CONF_PATH

SATOSHIS = 100_000_000
networks = ["mainnet", "testnet", "regtest"]


class BitcoinProxy:
    def __init__(self, network="testnet"):
        self.btc_conf_file = BTC_CONF_PATH
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
