import os
import struct
import traceback
import zlib
from io import BytesIO
from threading import Thread
from time import sleep

import bitcoin
import bitcoin.core
import bitcoin.rpc
import goTenna
import requests
from bitcoin.core import CMutableTransaction, CMutableTxOut, b2lx, b2x, lx, x
from bitcoin.wallet import CBitcoinAddress

from lntenna.gotenna_core.events import Events
from lntenna.txtenna_utilities.txtenna_segment import TxTennaSegment
from lntenna.txtenna_utilities.segment_storage import SegmentStorage

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
        self.segment_storage = SegmentStorage()
        self.send_dir = None
        self.receive_dir = None
        self.watch_dir_thread = None
        self.pipe_file = None
        self.gid = (None,)
        self.geo_region = None
        self.events = Events()
        self.btc_conf_file = None
        self._btc_network = "mainnet"
        bitcoin.SelectParams(self._btc_network)

    @property
    def btc_network(self):
        return self._btc_network

    @btc_network.setter
    def btc_network(self, network):
        """
        :param network: one of "mainnet", "testnet" or "regtest"  only
        """
        bitcoin.SelectParams(network)
        self._btc_network = network

    def reset(self):
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
                return (None, __gid)
            gidobj = goTenna.settings.GID(__gid, gid_type)
            return (gidobj, None)
        except ValueError:
            if print_message:
                print("{} is not a valid GID.".format(__gid))
            return (None, None)

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

    ###################
    # TxTenna methods #
    ###################

    # TODO: add set_network() and set_btc_conf_file() calls

    def rpc_getrawtransaction(self, tx_id):
        """
        Call local Bitcoin RPC method 'getrawtransaction'
        """
        proxy = bitcoin.rpc.RawProxy(btc_conf_file=self.btc_conf_file)
        tx_info = proxy.getrawtransaction(tx_id, True)
        return tx_info

    def confirm_bitcoin_tx_local(self, _hash, sender_gid, timeout=30):
        """
        Confirm bitcoin transaction using local bitcoind instance
        """
        result = {}

        # send transaction to local bitcoind
        segments = self.segment_storage.get_by_transaction_id(_hash)
        raw_tx = self.segment_storage.get_raw_tx(segments)

        # pass hex string converted to bytes
        try:
            proxy1 = bitcoin.rpc.Proxy(btc_conf_file=self.btc_conf_file)
            raw_tx_bytes = x(raw_tx)
            tx = CMutableTransaction.stream_deserialize(BytesIO(raw_tx_bytes))
            r1 = proxy1.sendrawtransaction(tx)
        except:
            result["send_status"] = "Invalid Transaction! Could not send to network."
            return result

        # try for `timeout` minutes to confirm the transaction
        for n in range(0, timeout):
            try:
                proxy2 = bitcoin.rpc.Proxy(btc_conf_file=self.btc_conf_file)
                r2 = proxy2.getrawtransaction(r1, True)

                # send zero-conf message back to tx sender
                confirmations = r2.get("confirmations", 0)
                rObj = TxTennaSegment("", "", tx_hash=_hash, block=confirmations)
                arg = str(sender_gid) + " " + rObj.serialize_to_json()
                self.send_private(arg)

                result["send_status"] = {
                    "Sent to GID": str(sender_gid),
                    "txid": _hash,
                    "status": "added to the mempool",
                }
                break
            except IndexError:
                # tx_id not yet in the global mempool, sleep for a minute then try again
                sleep(60)
                continue

                # wait for at least one confirmation
            for m in range(0, 30):
                sleep(60)  # sleep for a minute
                try:
                    proxy3 = bitcoin.rpc.Proxy(btc_conf_file=self.btc_conf_file)
                    r3 = proxy3.getrawtransaction(r1, True)
                    confirmations = r3.get("confirmations", 0)
                    # keep waiting until 1 or more confirmations
                    if confirmations > 0:
                        break
                except:
                    # unknown RPC error, but keep trying
                    traceback.print_exc()

            if confirmations > 0:
                # send confirmations message back to tx sender if confirmations > 0
                rObj = TxTennaSegment("", "", tx_hash=_hash, block=confirmations)
                arg = str(sender_gid) + " " + rObj.serialize_to_json()
                self.send_private(arg)
                result["confirmation_status"] = {
                    "transaction_from_gid": str(sender_gid),
                    "txid": _hash,
                    "status": "confirmed",
                    "num_confirmations": str_confirmations,
                }
            else:
                result["confirmation_status"] = {
                    "transaction_from_gid": str(sender_gid),
                    "txid": _hash,
                    "status": "unconfirmed",
                    "detail": "after 30 minutes",
                }

    @staticmethod
    def create_output_data_struct(data):
        """Create the output data structure generated by the blocksat receiver

        The "Protocol Sink" block of the blocksat-rx application places the incoming
        API data into output structures. This function creates the exact same
        structure that the blocksat-rx application would.

        Args:
            data : Sequence of bytes to be placed in the output structure

        Returns:
            Output data structure as sequence of bytes

        """

        # Header of the output data structure that the Blockstream Satellite Receiver
        # generates prior to writing user data into the API named pipe
        OUT_DATA_HEADER_FORMAT = "64sQ"
        OUT_DATA_DELIMITER = (
                "vyqzbefrsnzqahgdkrsidzigxvrppato"
                + '\xe0\xe0$\x1a\xe4["\xb5Z\x0bv\x17\xa7\xa7\x9d'
                + "\xa5\xd6\x00W}M\xa6TO\xda7\xfaeu:\xac\xdc"
        )

        # Struct is composed of a delimiter and the message length
        out_data_header = struct.pack(
                OUT_DATA_HEADER_FORMAT, OUT_DATA_DELIMITER, len(data)
        )

        # Final output data structure
        out_data = out_data_header + data

        return out_data

    def receive_message_from_gateway(self, filename):
        """
        Receive message data from a mesh gateway node

        Usage: receive_message_from_gateway filename
        """
        result = {}

        # send transaction to local blocksat reader pipe
        segments = self.segment_storage.get_by_transaction_id(filename)
        raw_data = self.segment_storage.get_raw_tx(segments).encode("utf-8")

        decoded_data = zlib.decompress(raw_data.decode("base64"))

        delimited_data = self.create_output_data_struct(decoded_data)

        # send the data to the blocksat pipe
        try:
            result = {
                "filename": filename,
                "length_bytes": str(len(decoded_data)),
                "unicode": True,
                "data": str(decoded_data),
            }
        except UnicodeDecodeError:
            result = {
                "filename": filename,
                "unicode": False,
                "length_bytes": str(len(decoded_data)),
            }

        if self.pipe_file is not None and os.path.exists(self.pipe_file) is True:
            # Open pipe and write raw data to it
            pipe_f = os.open(self.pipe_file, os.O_RDWR)
            os.write(pipe_f, delimited_data)
            result["status"] = "success"
        elif self.receive_dir is not None and os.path.exists(self.receive_dir) is True:
            # Create file
            dump_f = os.open(
                    os.path.join(self.receive_dir, filename), os.O_CREAT | os.O_RDWR
            )
            os.write(dump_f, decoded_data)
            result["status"] = "success"
        else:
            result["status"] = "failure"
            result["failure"] = {
                "pipe_missing_at": self.pipe_file,
                "recv_dir_missing": self.receive_dir,
            }
        return result

    def handle_message(self, message):
        """ handle a txtenna message received over the mesh network

        Usage: handle_message message
        """
        result = {}
        payload = str(message.payload.message)
        result["payload"] = payload

        segment = TxTennaSegment.deserialize_from_json(payload)
        self.segment_storage.put(segment)
        network = self.segment_storage.get_network(segment.payload_id)

        # process incoming transaction confirmation from another server
        if segment.block > 0:
            result["segment"] = {
                "txid": segment.payload_id,
                "status": "confirmed",
                "confirmed_in_block": segment.block,
            }
        elif segment.block is 0:
            result["segment"] = {
                "txid": segment.payload_id,
                "status": "added to the mempool",
            }
        elif network is "d":
            # process message data
            if self.segment_storage.is_complete(segment.payload_id):
                filename = self.segment_storage.get_transaction_id(segment.payload_id)
                t = Thread(target=self.receive_message_from_gateway, args=(filename,))
                result["message"] = t.start()
        else:
            # process incoming tx segment
            if not self.local:
                headers = {u"content-type": u"application/json"}
                url = (
                    "https://api.samouraiwallet.com/v2/txtenna/segments"
                )  # default txtenna-server
                r = requests.post(url, headers=headers, data=payload)
                result["process_segment"] = r.json()

            if self.segment_storage.is_complete(segment.payload_id):
                sender_gid = message.sender.gid_val
                tx_id = self.segment_storage.get_transaction_id(segment.payload_id)

                # check for confirmed transaction in a new thread
                if self.local:
                    t = Thread(
                            target=self.confirm_bitcoin_tx_local,
                            args=(tx_id, sender_gid)
                    )
                else:
                    t = Thread(
                            target=self.confirm_bitcoin_tx_online,
                            args=(tx_id, sender_gid, network),
                    )
                result["confirm_check"] = t.start()
        return result

    def mesh_broadcast_rawtx(self, str_hex_tx, str_hex_tx_hash, network):
        """
        Broadcast the raw hex of a Bitcoin transaction and its transaction ID over
        mainnet or testnet.
        A local copy of txtenna-server must be configured to support the selected
        network.

        Usage: mesh_broadcast_tx RAW_HEX TX_ID NETWORK(m|t)

        eg. txTenna> mesh_broadcast_rawtx 01000000000101bf6c3ed233e8700b42c1369993c2078780015bab7067b9751b7f49f799efbffd0000000017160014f25dbf0eab0ba7e3482287ebb41a7f6d361de6efffffffff02204e00000000000017a91439cdb4242013e108337df383b1bf063561eb582687abb93b000000000017a9148b963056eedd4a02c91747ea667fc34548cab0848702483045022100e92ce9b5c91dbf1c976d10b2c5ed70d140318f3bf2123091d9071ada27a4a543022030c289d43298ca4ca9d52a4c85f95786c5e27de5881366d9154f6fe13a717f3701210204b40eff96588033722f487a52d39a345dc91413281b31909a4018efb330ba2600000000, 94406beb94761fa728a2cde836ca636ecd3c51cbc0febc87a968cb8522ce7cc1, m
        """

        evt_start_len = self.events.callback.qsize()
        # TODO: test Z85 binary encoding and add as an option
        gid = self.api_thread.gid.gid_val
        segments = TxTennaSegment.tx_to_segments(
                gid, str_hex_tx, str_hex_tx_hash, str(self.messageIdx), network, False
        )
        for seg in segments:
            self.send_broadcast(seg.serialize_to_json())
            sleep(10)
        self.messageIdx = (self.messageIdx + 1) % 9999
        # wait_for(lambda: self.events.callback.qsize() > evt_start_len)
        result = []
        while self.events.callback.qsize() > evt_start_len:
            result.append(self.events.callback.get())
        return result

    def rpc_getbalance(self):
        """
        Call local Bitcoin RPC method 'getbalance'

        Usage: rpc_getbalance
        """
        result = {"getbalance": None}
        try:
            proxy = bitcoin.rpc.Proxy(btc_conf_file=self.btc_conf_file)
            return proxy.getbalance()
        except Exception:  # pylint: disable=broad-except
            return str(traceback.print_exc())

    def rpc_sendrawtransaction(self, _hex):
        """
        Call local Bitcoin RPC method 'sendrawtransaction'

        Usage: rpc_sendrawtransaction RAW_TX_HEX
        """
        try:
            proxy = bitcoin.rpc.Proxy(btc_conf_file=self.btc_conf_file)
            return proxy.sendrawtransaction(_hex)
        except Exception:  # pylint: disable=broad-except
            return str(traceback.print_exc())

    def rpc_sendtoaddress(self, addr, amount):
        """
        Call local Bitcoin RPC method 'sendtoaddress'

        Usage: rpc_sendtoaddress ADDRESS SATS
        """
        try:
            proxy = bitcoin.rpc.Proxy(btc_conf_file=self.btc_conf_file)
            return proxy.sendtoaddress(addr, amount)
        except Exception:  # pylint: disable=broad-except
            return str(traceback.print_exc())

    def mesh_sendtoaddress(self, addr, sats, network):
        """
        Create a signed transaction and broadcast it over the connected mesh device.
        The transaction spends some amount of satoshis to the specified address from the
        local bitcoind wallet and selected network.

        Usage: mesh_sendtoaddress ADDRESS SATS NETWORK(m|t)

        eg. txTenna> mesh_sendtoaddress 2N4BtwKZBU3kXkWT7ZBEcQLQ451AuDWiau2 13371337 t
        """
        result = {}
        try:

            proxy = bitcoin.rpc.Proxy(btc_conf_file=self.btc_conf_file)

            # Create the txout. This time we create the scriptPubKey from a Bitcoin
            # address.
            txout = CMutableTxOut(sats, CBitcoinAddress(addr).to_scriptPubKey())

            # Create the unsigned transaction.
            unfunded_transaction = CMutableTransaction([], [txout])
            funded_transaction = proxy.fundrawtransaction(unfunded_transaction)
            signed_transaction = proxy.signrawtransaction(funded_transaction["tx"])
            txhex = b2x(signed_transaction["tx"].serialize())
            txid = b2lx(signed_transaction["tx"].GetTxid())
            result["transaction_created"] = {
                "tx_hex": txhex,
                "txid": txid,
                "network": network,
            }

            # broadcast over mesh
            result["mesh_broadcast"] = self.mesh_broadcast_rawtx(
                    txhex + " " + txid + " " + network
            )

        except Exception:  # pylint: disable=broad-except
            result["exception_raised"] = str(traceback.print_exc())

        try:
            # lock UTXOs used to fund the tx if broadcast successful
            vin_outpoints = set()
            for txin in funded_transaction["tx"].vin:
                vin_outpoints.add(txin.prevout)
            # json_outpoints = [{'txid':b2lx(outpoint.hash), 'vout':outpoint.n}
            #              for outpoint in vin_outpoints]
            # print(str(json_outpoints))
            proxy2 = bitcoin.rpc.Proxy(btc_conf_file=self.btc_conf_file)
            proxy2.lockunspent(False, vin_outpoints)

        except Exception:  # pylint: disable=broad-except
            # TODO: figure out why this is happening
            # TODO: added a second proxy object above to prevent rpc failures
            print("RPC timeout after calling lockunspent")

    def broadcast_messages(self, send_dir):
        """
        Watch a particular directory for files with message data to be broadcast over
        the mesh network

        Usage: broadcast_messages DIRECTORY

        eg. txTenna> broadcast_messages ./downloads
        """

        if send_dir is not None:
            # start new thread to watch directory
            self.watch_dir_thread = Thread(
                    target=self.watch_messages, args=(self, send_dir)
            )
            self.watch_dir_thread.start()
            return {"watching_dir": send_dir}

    def watch_messages(self, send_dir):
        before = {}
        while os.path.exists(send_dir):
            sleep(10)
            after = dict([(f, None) for f in os.listdir(send_dir)])
            new_files = [f for f in after if f not in before]
            if new_files:
                self.broadcast_message_files(self, send_dir, new_files)
            before = after

    def broadcast_message_files(self, directory, filenames):
        for filename in filenames:
            # print("Broadcasting ", directory + "/" + filename)
            f = open(directory + "/" + filename, "r")
            message_data = f.read()
            f.close()

            # binary to ascii encoding and strip out newlines
            encoded = zlib.compress(message_data, 9).encode("base64").replace("\n", "")
            # print("[\n" + encoded.decode() + "\n]")

            gid = self.api_thread.gid.gid_val
            segments = TxTennaSegment.tx_to_segments(
                    gid, encoded, filename, str(self.messageIdx), "d", False
            )
            for seg in segments:
                self.send_broadcast(seg.serialize_to_json())
                sleep(10)
            self.messageIdx = (self.messageIdx + 1) % 9999
