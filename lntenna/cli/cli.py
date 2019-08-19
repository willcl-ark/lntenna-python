#! usr/bin/python

import cmd
import simplejson as json

from lntenna.gotenna.connection import Connection


class Lntenna(cmd.Cmd):
    intro = (
        "Send a Blockstream Blocksat message using GoTenna meshnet. "
        "Type help or ? to list commands.\n"
    )
    prompt = "(lntenna) "

    def __init__(self, conn):
        self.conn = conn
        self.sdk_token = None
        self.GID = None
        self.geo_region = None
        self.config = False
        super().__init__()
        self.check_for_config()

    def check_for_config(self):
        try:
            from lntenna.server.config import CONFIG
            if CONFIG["gotenna"]:
                print("Config file found, loading SDK_TOKEN, GID and GEO_REGION")
                self.conn.sdk_token(CONFIG["gotenna"]["SDK_TOKEN"])
                self.conn.set_gid(int(CONFIG["gotenna"]["GID"]))
                self.conn.set_geo_region(int(CONFIG["gotenna"]["GEO_REGION"]))
                self.config = True
                print("Config values set successfully")
        except Exception:
            pass

    def do_sdk_token(self, arg):
        """Set SDK Token for the connection
        :arg sdk_token
        """
        self.conn.sdk_token(arg)
        print(f"SDK token set: {self.conn.api_thread.sdk_token.decode('utf-8')}")

    def do_set_gid(self, arg):
        """Set GID for the GoTenna device
        :arg GID
        """
        arg = int(arg)
        self.conn.set_gid(arg)
        print(f"GID set: {self.conn.api_thread.gid.gid_val}")

    def do_set_geo_region(self, arg):
        """Set geo_region for the GoTenna device:
        :arg geo_region
        """
        arg = int(arg)
        self.conn.set_geo_region(arg)
        print(f"geo_region set: {self.conn.api_thread.geo_settings.region}")

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
        You will be prompted for further details
        Network must be either 'mainnet' or 'testnet'
        """
        if arg == '':
            message = input("Message: ")
            addr = input("Refund bitcoin address: ")
            network = input("Network:")
            assert network == "mainnet" or "testnet"
            n = "m" if network is "mainnet" else "t"

            req = {"sat_req":
                       {"m": message,
                        "a": addr,
                        "n": n
                        }
                   }

            self.conn.send_broadcast(json.dumps(req))


    @staticmethod
    def do_hello(s):
        """Say hello to you"""
        if s == "":
            s = input("Your name please: ")
        print(f"Hello, {s}")

    @staticmethod
    def do_exit(arg):
        """Exit cli app
        """
        print("Goodbye")
        return True


def parse(arg):
    """Convert a series of zero or more numbers to an argument tuple
    """
    return tuple(map(int, arg.split()))


if __name__ == "__main__":
    connection = Connection()
    Lntenna(conn=connection).cmdloop()
