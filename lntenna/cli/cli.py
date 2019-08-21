#! usr/bin/python

import cmd
import simplejson as json
from pprint import pformat

from lntenna.gotenna.connection import Connection
from lntenna.database.db import cli_lookup_swap_tx


class Lntenna(cmd.Cmd):
    intro = (
        "Send a Blockstream Blocksat message using GoTenna meshnet. "
        "Type help or ? to list commands.\n"
    )
    prompt = "(lntenna) "

    def __init__(self, conn):
        self.conn = conn
        self.conn.cli = True
        self.sdk_token = None
        self.GID = None
        self.geo_region = None
        self.config = False
        self.refund_address = None
        self.network = None
        super().__init__()
        self.check_for_config()

    def emptyline(self):
        print("\n")

    def check_for_config(self):
        try:
            from lntenna.server.config import CONFIG

            if CONFIG["gotenna"] or CONFIG["bitcoin"]:
                print("Config file found, loading values")
                if CONFIG["gotenna"]["SDK_TOKEN"]:
                    self.conn.sdk_token(CONFIG["gotenna"]["SDK_TOKEN"])
                if CONFIG["gotenna"]["GID"]:
                    self.conn.set_gid(int(CONFIG["gotenna"]["GID"]))
                if CONFIG["gotenna"]["GEO_REGION"]:
                    self.conn.set_geo_region(int(CONFIG["gotenna"]["GEO_REGION"]))
                if CONFIG["bitcoin"]["BTC_NETWORK"]:
                    self.network = CONFIG["bitcoin"]["BTC_NETWORK"]
                if CONFIG["bitcoin"]["REFUND_ADDR"]:
                    self.refund_address = CONFIG["bitcoin"]["REFUND_ADDR"]
                self.config = True
                print("Config values set successfully")
        except Exception:
            pass

    def do_sdk_token(self, arg):
        """Set SDK Token for the connection
        :arg sdk_token
        """
        self.conn.sdk_token(arg)
        # print(f"SDK token set: {self.conn.api_thread.sdk_token.decode('utf-8')}")

    def do_set_gid(self, arg):
        """Set GID for the GoTenna device
        :arg GID
        """
        arg = int(arg)
        self.conn.set_gid(arg)

    def do_set_geo_region(self, arg):
        """Set geo_region for the GoTenna device:
        :arg geo_region
        """
        arg = int(arg)
        self.conn.set_geo_region(arg)
        # print(f"geo_region set: {self.conn.api_thread.geo_settings.region}")

    def do_can_connect(self, arg):
        """Return whether a GoTenna can connect
        For a GoTenna to connect, a GID and RF setting must be configured
        """
        self.conn.can_connect()

    def do_get_device_type(self, arg):
        """Return the device type
        """
        self.conn.get_device_type()

    def do_get_system_info(self, arg):
        """Return the system info
        """
        self.conn.get_system_info()

    def do_send_broadcast(self, arg):
        """Send a broadcast message to all nearby GoTenna devices
        :arg message

        If no message is provided as argument, you will be provided with a prompt to
        enter your message
        """
        if arg == "":
            arg = input("Message: ")
        self.conn.send_broadcast(arg)

    def do_send_sat_msg(self, arg):
        """Send a message via the Blockstream Blocksat
        You will be prompted for additional details
        Network must be either exactly 'mainnet' or 'testnet'
        """
        if arg == "":
            message = input("Message: ")
            if self.refund_address:
                res = input(
                    f"Do you want to use bitcoin address "
                    f"{self.refund_address} from config file? y/n\t"
                )
                if res.lower() == "y":
                    addr = self.refund_address
            else:
                addr = input("Refund bitcoin address: ")
            if self.network:
                res = input(
                    f'Do you want to use network "{self.network}" from config'
                    f" file? y/n\t"
                )
                if res.lower() == "y":
                    network = self.network
            else:
                network = input("Network:")
            assert network.lower() == "mainnet" or "testnet"
            n = "m" if network.lower() is "mainnet" else "t"

            req = {"sat_req": {"m": message, "a": addr, "n": n}}

            # send it via regular broadcast or jumbo depending on size
            if len(message) < 200:
                try:
                    self.conn.send_broadcast(json.dumps(req))
                except Exception as e:
                    print(
                        f"send_broadcast raised exception {e}, retrying with "
                        f"send_jumbo"
                    )
                    self.conn.send_jumbo(json.dumps(req))
            else:
                self.conn.send_jumbo(json.dumps(req))

    def do_resend_swap_tx(self, arg):
        """Resend the "swap_tx" message to the gateway for the specified UUID
        :arg UUID
        """
        uuid = str(arg)
        tx_hash, tx_hex = cli_lookup_swap_tx(uuid)
        swap_tx_msg = {"swap_tx": {"tx_hash": tx_hash, "tx_hex": tx_hex, "uuid": uuid}}
        print(f"Successfully looked up swap in the db:\n{pformat(swap_tx_msg)}")
        self.conn.send_jumbo(swap_tx_msg)

    def do_lookup_order(self, uuid):
        """Lookup order details for a provided lntenna UUID

        :param uuid: str
        """
        uuid = str(uuid)
        order = cli_lookup_uuid(uuid)
        pprint(order)

    @staticmethod
    def do_exit(arg):
        """Exit cli app
        """
        print("Goodbye")
        return True


if __name__ == "__main__":
    connection = Connection()
    Lntenna(conn=connection).cmdloop()
