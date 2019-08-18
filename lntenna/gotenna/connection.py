import traceback
import logging
import requests
import threading
from time import sleep, time
import simplejson as json
import types

import goTenna

import lntenna.txtenna as txtenna
from lntenna.gotenna.events import Events
from lntenna.bitcoin.rpc import BitcoinProxy
from lntenna.api.message_codes import MSG_CODES
from lntenna.swap.auto_swap_create import auto_swap
from lntenna.swap.auto_swap_complete import auto_swap_complete
from lntenna.swap.auto_swap_verify import auto_swap_verify
from lntenna.gotenna.utilities import prepare_api_request, segment, de_segment

logger = logging.getLogger(__name__)
FORMAT = "[%(levelname)s - %(funcname)s] - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
logging.getLogger("goTenna").setLevel(logging.CRITICAL)

# For SPI connection only, set SPI_CONNECTION to true with proper SPI settings
SPI_CONNECTION = False
SPI_BUS_NO = 0
SPI_CHIP_NO = 0
SPI_REQUEST = 22
SPI_READY = 27


class Connection:
    def __init__(self):
        self.api_thread = None
        self.status = {}
        self.in_flight_events = {}
        self._set_frequencies = False
        self._set_tx_power = False
        self._set_bandwidth = False
        self._set_geo_region = False
        self._settings = goTenna.settings.GoTennaSettings(
            rf_settings=goTenna.settings.RFSettings(),
            geo_settings=goTenna.settings.GeoSettings(),
        )
        self._do_encryption = True
        self._awaiting_disconnect_after_fw_update = [False]
        self.messageIdx = 0
        self.local = False
        self.segment_storage = txtenna.SegmentStorage()
        self.send_dir = None
        self.receive_dir = None
        self.watch_dir_thread = None
        self.pipe_file = None
        self.gid = (None,)
        self.geo_region = None
        self.events = Events()
        self.btc = BitcoinProxy()
        self.gateway = 0
        # self.jumbo_thread = None
        # self.jumbo_thread = threading.Thread(
        #     target=self.monitor_jumbo_msgs, daemon=True
        # )

    @property
    def jumbo_thread(self):
        return threading.Thread(
                target=self.monitor_jumbo_msgs, daemon=True
        )

    def reset_connection(self):
        if self.api_thread:
            self.api_thread.join()
        self.__init__()

    def sdk_token(self, sdk_token):
        """set sdk_token for the connection
        """
        if self.api_thread:
            print("To change SDK tokens, restart the sample app.")
            return
        try:
            if not SPI_CONNECTION:
                self.api_thread = goTenna.driver.Driver(
                    sdk_token=sdk_token,
                    gid=None,
                    settings=None,
                    event_callback=self.event_callback,
                )
            else:
                self.api_thread = goTenna.driver.SpiDriver(
                    SPI_BUS_NO,
                    SPI_CHIP_NO,
                    22,
                    27,
                    sdk_token,
                    None,
                    None,
                    self.event_callback,
                )
            self.api_thread.start()
        except ValueError:
            print(
                "SDK token {} is not valid. Please enter a valid SDK token.".format(
                    sdk_token
                )
            )

    def event_callback(self, evt):
        """ The event callback that will store even messages from the API.
        See the documentation for ``goTenna.driver``.
        This will be invoked from the API's thread when events are received.
        """
        if evt.event_type == goTenna.driver.Event.MESSAGE:
            try:
                self.events.msg.put(evt)
                # TODO: check this affects txtenna only
                if self.gateway == 1:
                    thread = threading.Thread(
                        target=self.handle_message, args=[evt.message]
                    )
                    thread.start()
                    # self.handle_message(evt.message)
            except Exception:
                traceback.print_exc()
        elif evt.event_type == goTenna.driver.Event.DEVICE_PRESENT:
            self.events.device_present.put(evt)
            # TODO: Incorporate logic below into smart API responses
            if self._awaiting_disconnect_after_fw_update[0]:
                print("Device physically connected")
            else:
                print("Device physically connected, configure to continue")
        elif evt.event_type == goTenna.driver.Event.CONNECT:
            self.events.connect.put(evt)
            # TODO: Incorporate logic below into smart API responses
            if self._awaiting_disconnect_after_fw_update[0]:
                print("Device reconnected! Firmware update complete!")
                self._awaiting_disconnect_after_fw_update[0] = False
            else:
                print("Connected!")
        elif evt.event_type == goTenna.driver.Event.DISCONNECT:
            self.events.disconnect.put(evt)
            # TODO: Incorporate logic below into smart API responses
            if self._awaiting_disconnect_after_fw_update[0]:
                # Do not reset configuration so that the device will reconnect on its
                # own
                print("Firmware update: Device disconnected, awaiting reconnect")
            else:
                print("Disconnected! {}".format(evt))
                # We reset the configuration here so that if the user plugs in a
                # different device it is not immediately reconfigured with new and
                # incorrect data
                self.api_thread.set_gid(None)
                self.api_thread.set_rf_settings(None)
                self._set_frequencies = False
                self._set_tx_power = False
                self._set_bandwidth = False
        elif evt.event_type == goTenna.driver.Event.STATUS:
            self.status = evt.status
            self.events.status.put(evt)
        elif evt.event_type == goTenna.driver.Event.GROUP_CREATE:
            index = -1
            for idx, member in enumerate(evt.group.members):
                if member.gid_val == self.api_thread.gid.gid_val:
                    index = idx
                    break
            print(
                "Added to group {}: You are member {}".format(
                    evt.group.gid.gid_val, index
                )
            )
            self.events.group_create.put(evt)

    def build_callback(self, error_handler=None):
        """ Build a callback for sending to the API thread. May specify a callable
        error_handler(details) taking the error details from the callback.
        The handler should return a string.
        """

        def default_error_handler(details):
            """ Easy error handler if no special behavior is needed.
            Just builds a string with the error.
            """
            if details["code"] in [
                goTenna.constants.ErrorCodes.TIMEOUT,
                goTenna.constants.ErrorCodes.OSERROR,
                goTenna.constants.ErrorCodes.EXCEPTION,
            ]:
                return "USB connection disrupted"
            return "Error: {}: {}".format(details["code"], details["msg"])

        # Define a second function here so it implicitly captures self
        captured_error_handler = [error_handler]

        def callback(
            correlation_id, success=None, results=None, error=None, details=None
        ):
            """ The default callback to pass to the API.
            See the documentation for ``goTenna.driver``.
            Does nothing but print whether the method succeeded or failed.
            """
            method = self.in_flight_events.pop(correlation_id.bytes, "Method call")
            if success:
                if results:
                    print("{} succeeded: {}".format(method, results))
                    self.events.callback.put(
                        {"method": method, "results": results, "status": "Success"}
                    )
                else:
                    print("{} succeeded!".format(method))
                    self.events.callback.put({"method": method, "status": "success"})
            elif error:
                if not captured_error_handler[0]:
                    captured_error_handler[0] = default_error_handler
                print(
                    "{} failed: {}".format(method, captured_error_handler[0](details))
                )
                self.events.callback.put(
                    {
                        "method": method,
                        "error_details": captured_error_handler[0](details),
                        "status": "failed",
                    }
                )

        return callback

    def set_gid(self, gid):
        """ Create a new profile (if it does not already exist) with default settings.
        GID should be a 15-digit numerical GID.
        """
        if self.api_thread.connected:
            print("Must not be connected when setting GID")
            return
        (_gid, _) = self._parse_gid(gid, goTenna.settings.GID.PRIVATE)
        if not _gid:
            return
        self.api_thread.set_gid(_gid)
        self._settings.gid_settings = gid

    def send_broadcast(self, message):
        """ Send a broadcast message
        """
        if not self.api_thread.connected:
            print("No device connected")
        else:

            def error_handler(details):
                """ A special error handler for formatting message failures
                """
                if details["code"] in [
                    goTenna.constants.ErrorCodes.TIMEOUT,
                    goTenna.constants.ErrorCodes.OSERROR,
                ]:
                    return "Message may not have been sent: USB connection disrupted"
                return "Error sending message: {}".format(details)

            try:
                method_callback = self.build_callback(error_handler)
                payload = goTenna.payload.TextPayload(message)
                print(
                    "payload valid = {}, message size = {}\n".format(
                        payload.valid, len(message)
                    )
                )

                corr_id = self.api_thread.send_broadcast(payload, method_callback)
                while corr_id is None:
                    # try again if send_broadcast fails
                    sleep(10)
                    corr_id = self.api_thread.send_broadcast(payload, method_callback)

                self.in_flight_events[
                    corr_id.bytes
                ] = "Broadcast message: {} ({} bytes)\n".format(message, len(message))
            except ValueError:
                print("Message too long!")
                return

    @staticmethod
    def _parse_gid(__gid, gid_type, print_message=True):
        try:
            if __gid > goTenna.constants.GID_MAX:
                print(
                    "{} is not a valid GID. The maximum GID is {}".format(
                        str(__gid), str(goTenna.constants.GID_MAX)
                    )
                )
                return None, __gid
            gidobj = goTenna.settings.GID(__gid, gid_type)
            return gidobj, None
        except ValueError:
            if print_message:
                print("{} is not a valid GID.".format(__gid))
            return None, None

    def send_private(self, gid, message):
        """ Send a private message to a contact
        GID is the GID to send the private message to.
        """
        if not self.api_thread.connected:
            print("Must connect first")
            return
        if not gid:
            return

        def error_handler(details):
            """ Special error handler for sending private messages to format errors
            """
            return "Error sending message: {}".format(details)

        try:
            method_callback = self.build_callback(error_handler)
            payload = goTenna.payload.TextPayload(message)

            def ack_callback(correlation_id, success):
                if success:
                    print(
                        "Private message to {}: delivery confirmed".format(gid.gid_val)
                    )
                else:
                    print(
                        "Private message to {}: delivery not confirmed, recipient may"
                        " be offline or out of range".format(gid.gid_val)
                    )

            corr_id = self.api_thread.send_private(
                gid,
                payload,
                method_callback,
                ack_callback=ack_callback,
                encrypt=self._do_encryption,
            )
        except ValueError:
            print("Message too long!")
            return
        self.in_flight_events[corr_id.bytes] = "Private message to {}: {}".format(
            gid.gid_val, message
        )

    def send_jumbo(self, message, segment_size=210, private=False, gid=None):
        msg_segments = segment(message, segment_size)
        if not private:
            for msg in msg_segments:
                sleep(2)
                self.send_broadcast(msg)
            return
        return
        # disabled for now as requires custom message parsing
        # TODO: enable private messages here
        # if not gid:
        #     print("Missing GID")
        #     return
        # gid = goTenna.settings.GID(gid, 0)
        # for msg in msg_segments:
        #     self.send_private(gid, msg)

    def get_device_type(self):
        return self.api_thread.device_type

    @staticmethod
    def list_geo_region():
        """ List the available region.
        """
        return goTenna.constants.GEO_REGION.DICT

    def set_geo_region(self, region):
        """ Configure the frequencies the device will use.
        Allowed region displayed with list_geo_region.
        """
        if self.get_device_type() == "pro":
            print("This configuration cannot be done for Pro devices.")
            return
        print("region={}".format(region))
        if not goTenna.constants.GEO_REGION.valid(region):
            print("Invalid region setting {}".format(region))
            return
        self._set_geo_region = True
        self._settings.geo_settings.region = region
        self.api_thread.set_geo_settings(self._settings.geo_settings)

    def can_connect(self):
        """ Return whether a goTenna can connect.
        For a goTenna to connect, a GID and RF settings must be configured.
        """
        result = {}
        if self.api_thread.gid:
            result["GID"] = "OK"
        else:
            result["GID"] = "Not Set"
        if self._set_tx_power:
            result["PRO - TX Power"] = "OK"
        else:
            result["PRO - TX Power"] = "Not Set"
        if self._set_frequencies:
            result["PRO - Frequencies"] = "OK"
        else:
            result["PRO - Frequencies"] = "Not Set"
        if self._set_bandwidth:
            result["PRO - Bandwidth"] = "OK"
        else:
            result["PRO - Bandwidth"] = "Not Set"
        if self._set_geo_region:
            result["MESH - Geo region"] = "OK"
        else:
            result["MESH - Geo region"] = "Not Set"
        return result

    def get_system_info(self):
        """ Get system information.
        """
        if not self.api_thread.connected:
            return "Device must be connected"
        return self.api_thread.system_info

    def handle_message(self, message):
        """ handle a txtenna message received over the mesh network

        Usage: handle_message message
        """

        payload = message.payload.message
        logger.debug(
            f"Handle message received message {payload} of type {type(payload)}"
        )
        # handle a jumbo message
        try:
            if payload.startswith("sm/"):
                # TODO: this cuts out all sender and receiver info -- ADD SENDER GID
                if self.jumbo_thread.is_alive():
                    pass
                else:
                    self.jumbo_thread.start()
                self.events.jumbo.append(payload)
                a, b, c, m = payload.split("/")
                self.events.jumbo_len = c
                return
        except Exception as e:
            logger.debug("handle_message() did not detect a jumbo message")
            logger.debug(e)

        # handle a known message type defined in MSG_CODES
        try:
            payload = json.loads(payload)
            logger.debug(
                f"handle_message() loaded a json-formatted message:\n{payload} which is now type: {type(payload)}"
            )
            if isinstance(payload, str):
                json.loads(payload)
            for k, v in payload.items():
                if k in MSG_CODES:
                    # pass the full request dict through to parse message type later
                    return self.handle_non_txtenna_msg(payload)
            # return self.handle_txtenna_message(payload)
        except Exception as e:
            logger.debug(e)

    def handle_non_txtenna_msg(self, message):
        for k, v in message.items():
            if k == "api_request":
                # pass the request dict only through
                prepped = prepare_api_request(v)
                with requests.Session() as s:
                    return s.send(prepped, timeout=30)
            if k == "sat_req":
                # do an automatic blocksat and swap setup
                data = json.dumps(auto_swap(v))
                logger.debug(data)
                self.send_jumbo(data)
            if k == "sat_fill":
                print(f"sat_fill received!!!: {v}")
                swap_paid = auto_swap_verify(v, self.btc.raw_proxy)
                self.send_jumbo(json.dumps(swap_paid))
            if k == "swap_tx":
                logger.debug("Processing a swap_tx message")
                swap_complete = auto_swap_complete(v["uuid"], v["tx_hex"], self)
                self.send_broadcast(json.dumps(swap_complete))

    def monitor_jumbo_msgs(self, timeout=60):
        logger.debug("starting monitoring jumbo messages")
        start = time()
        while True and time() < start + timeout:
            logger.debug(
                f"received: {len(self.events.jumbo)} of {self.events.jumbo_len} jumbo messages"
            )
            if (
                len(self.events.jumbo) == int(self.events.jumbo_len)
                and len(self.events.jumbo) is not 0
            ):
                # give handle_message the attributes it expects
                jumbo_message = types.SimpleNamespace()
                jumbo_message.payload = types.SimpleNamespace()
                # reconstruct the jumbo message
                jumbo_message.payload.message = json.loads(
                    de_segment(self.events.jumbo)
                )
                # send it back through handle_message
                logger.debug(f"jumbo_message_payload = {jumbo_message.payload.message}")
                self.handle_message(jumbo_message)
                break
            sleep(5)
        # reset jumbo events after timeout
        self.events.init_jumbo()
        return

    ###########
    # txtenna #
    ###########

    def rpc_getrawtransaction(self, tx_id):
        return txtenna.rpc_getrawtransaction(self, tx_id)

    def confirm_bitcoin_tx_local(self, _hash, sender_gid, timeout=30):
        return txtenna.confirm_bitcoin_tx_local(self, _hash, sender_gid, timeout)

    @staticmethod
    def create_output_data_struct(data):
        return txtenna.create_output_data_struct(data)

    def receive_message_from_gateway(self, filename):
        return txtenna.receive_message_from_gateway(self, filename)

    def handle_txtenna_message(self, message):
        return txtenna.handle_txtenna_message(self, message)

    def mesh_broadcast_rawtx(self, str_hex_tx, str_hex_tx_hash, network):
        return txtenna.mesh_broadcast_rawtx(self, str_hex_tx, str_hex_tx_hash, network)

    def rpc_getbalance(self):
        return txtenna.rpc_getbalance(self)

    def rpc_sendrawtransaction(self, tx_hex):
        return txtenna.rpc_sendrawtransaction(self, tx_hex)

    def rpc_sendtoaddress(self, addr, amount):
        return txtenna.rpc_sendtoaddress(self, addr, amount)

    def mesh_sendtoaddress(self, addr, sats, network):
        return txtenna.mesh_sendtoaddress(self, addr, sats, network)

    def broadcast_messages(self, send_dir):
        return txtenna.broadcast_messages(self, send_dir)

    def watch_messages(self, send_dir):
        return txtenna.watch_messages(self, send_dir)

    def broadcast_message_files(self, directory, filenames):
        return txtenna.broadcast_message_files(self, directory, filenames)
