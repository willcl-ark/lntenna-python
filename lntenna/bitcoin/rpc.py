import bitcoin
import bitcoin.core
import bitcoin.rpc
from lntenna.server.config import BTC_CONF_PATH


class BitcoinProxy:
    def __init__(self):
        self.btc_conf_file = BTC_CONF_PATH
        self._btc_network = "mainnet"
        bitcoin.SelectParams(self._btc_network)

    @property
    def network(self):
        return self._btc_network

    @network.setter
    def network(self, network):
        """
        :param network: one of "mainnet", "testnet" or "regtest"
        """
        self._btc_network = network
        bitcoin.SelectParams(self.network)

    @property
    def raw_proxy(self):
        return bitcoin.rpc.RawProxy(btc_conf_file=self.btc_conf_file)