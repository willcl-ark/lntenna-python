""" txtenna.py - 
This code is derived from sample.py available from the goTenna Public SDK (https://github.com/gotenna/PublicSDK)
"""
from __future__ import print_function

import logging
import os
import struct
import traceback
import zlib
from io import BytesIO
from threading import Thread
from time import sleep

import requests

from txtenna_segment import TxTennaSegment
import bitcoin
import bitcoin.rpc
from bitcoin.core import x, lx, b2x, b2lx, CMutableTxOut, CMutableTransaction
from bitcoin.wallet import CBitcoinAddress

from utilities import wait_for

bitcoin.SelectParams("mainnet")

# Configure the Python logging module to print to stderr. In your application,
# you may want to route the logging elsewhere.
logging.basicConfig()


TXTENNA_GATEWAY_GID = 2573394689


def rpc_getrawtransaction(tx_id):
    """
    Call local Bitcoin RPC method 'getrawtransaction'
    """
    proxy = bitcoin.rpc.Proxy()
    r = proxy.getrawtransaction(lx(tx_id), True)
    return str(r)


def confirm_bitcoin_tx_local(conn, _hash, sender_gid, timeout=30):
    """
    Confirm bitcoin transaction using local bitcoind instance
    """
    result = {}

    # send transaction to local bitcoind
    segments = conn.segment_storage.get_by_transaction_id(_hash)
    raw_tx = conn.segment_storage.get_raw_tx(segments)

    # pass hex string converted to bytes
    try:
        proxy1 = bitcoin.rpc.Proxy()
        raw_tx_bytes = x(raw_tx)
        tx = CMutableTransaction.stream_deserialize(BytesIO(raw_tx_bytes))
        r1 = proxy1.sendrawtransaction(tx)
    except:
        result["status"] = "Invalid Transaction! Could not send to network."
        return result

    # try for `timeout` minutes to confirm the transaction
    for n in range(0, timeout):
        try:
            proxy2 = bitcoin.rpc.Proxy()
            r2 = proxy2.getrawtransaction(r1, True)

            # send zero-conf message back to tx sender
            confirmations = r2.get("confirmations", 0)
            rObj = TxTennaSegment("", "", tx_hash=_hash, block=confirmations)
            arg = str(sender_gid) + " " + rObj.serialize_to_json()
            conn.send_private(arg)

            result["send status"] = {
                "Sent to GID": str(sender_gid),
                "txid": _hash,
                "status": "added to the mempool",
            }
            break
        except IndexError:
            # tx_id not yet in the global mempool, sleep for a minute and then try again
            sleep(60)
            continue

            # wait for atleast one confirmation
        for m in range(0, 30):
            sleep(60)  # sleep for a minute
            try:
                proxy3 = bitcoin.rpc.Proxy()
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
            conn.send_private(arg)
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
    out_data_header = struct.pack(OUT_DATA_HEADER_FORMAT, OUT_DATA_DELIMITER, len(data))

    # Final output data structure
    out_data = out_data_header + data

    return out_data


def receive_message_from_gateway(conn, filename):
    """ 
    Receive message data from a mesh gateway node

    Usage: receive_message_from_gateway filename
    """
    result = {}

    # send transaction to local blocksat reader pipe
    segments = conn.segment_storage.get_by_transaction_id(filename)
    raw_data = conn.segment_storage.get_raw_tx(segments).encode("utf-8")

    decoded_data = zlib.decompress(raw_data.decode("base64"))

    delimited_data = conn.create_output_data_struct(decoded_data)

    # send the data to the blocksat pipe
    try:
        result["message"] = {
            "filename": filename,
            "length_bytes": str(len(decoded_data)),
            "unicode": True,
            "data": str(decoded_data)
        }
    except UnicodeDecodeError:
        result["message"] = {
            "filename": filename,
            "unicode": False,
            "length_bytes": str(len(decoded_data))

        }

    if conn.pipe_file is not None and os.path.exists(conn.pipe_file) is True:
        # Open pipe and write raw data to it
        pipe_f = os.open(conn.pipe_file, os.O_RDWR)
        os.write(pipe_f, delimited_data)
        result["status"] = "success"
    elif conn.receive_dir is not None and os.path.exists(conn.receive_dir) is True:
        # Create file
        dump_f = os.open(
            os.path.join(conn.receive_dir, filename), os.O_CREAT | os.O_RDWR
        )
        os.write(dump_f, decoded_data)
        result["status"] = "success"
    else:
        result["status"] = "failure"
        result["failure"] = {
            "pipe_missing_at": conn.pipe_file,
            "recv_dir_missing": conn.receive_dir,
        }
    return result


def handle_message(conn, message):
    """ handle a txtenna message received over the mesh network

    Usage: handle_message message
    """
    result = {}
    payload = str(message.payload.message)
    result["payload"] = payload

    segment = TxTennaSegment.deserialize_from_json(payload)
    conn.segment_storage.put(segment)
    network = conn.segment_storage.get_network(segment.payload_id)

    # process incoming transaction confirmation from another server
    if segment.block > 0:
        result["segment"] = {
            "txid": segment.payload_id,
            "status": "confirmed",
            "confirmed_in_block": segment.block
        }
    elif segment.block is 0:
        result["segment"] = {
            "txid": segment.payload_id,
            "status": "added to the mempool"
        }
    elif network is "d":
        # process message data
        if conn.segment_storage.is_complete(segment.payload_id):
            filename = conn.segment_storage.get_transaction_id(segment.payload_id)
            t = Thread(target=conn.receive_message_from_gateway, args=(filename,))
            t.start()
    else:
        # TODO: This entire clause needs sorting!!!
        # process incoming tx segment
        if not conn.local:
            headers = {u"content-type": u"application/json"}
            url = (
                "https://api.samouraiwallet.com/v2/txtenna/segments"
            )  # default txtenna-server
            r = requests.post(url, headers=headers, data=payload)
            print(r.text)

        if conn.segment_storage.is_complete(segment.payload_id):
            sender_gid = message.sender.gid_val
            tx_id = conn.segment_storage.get_transaction_id(segment.payload_id)

            # check for confirmed transaction in a new thread
            if conn.local:
                t = Thread(
                    target=confirm_bitcoin_tx_local, args=(tx_id, sender_gid)
                )
            else:
                t = Thread(
                    target=conn.confirm_bitcoin_tx_online,
                    args=(tx_id, sender_gid, network),
                )
            t.start()


def mesh_broadcast_rawtx(conn, str_hex_tx, str_hex_tx_hash, network):
    """ 
    Broadcast the raw hex of a Bitcoin transaction and its transaction ID over mainnet
    or testnet.
    A local copy of txtenna-server must be configured to support the selected network.

    Usage: mesh_broadcast_tx RAW_HEX TX_ID NETWORK(m|t)

    eg. txTenna> mesh_broadcast_rawtx 01000000000101bf6c3ed233e8700b42c1369993c2078780015bab7067b9751b7f49f799efbffd0000000017160014f25dbf0eab0ba7e3482287ebb41a7f6d361de6efffffffff02204e00000000000017a91439cdb4242013e108337df383b1bf063561eb582687abb93b000000000017a9148b963056eedd4a02c91747ea667fc34548cab0848702483045022100e92ce9b5c91dbf1c976d10b2c5ed70d140318f3bf2123091d9071ada27a4a543022030c289d43298ca4ca9d52a4c85f95786c5e27de5881366d9154f6fe13a717f3701210204b40eff96588033722f487a52d39a345dc91413281b31909a4018efb330ba2600000000, 94406beb94761fa728a2cde836ca636ecd3c51cbc0febc87a968cb8522ce7cc1, m
    """

    evt_start_len = conn.events.callback.qsize()
    # TODO: test Z85 binary encoding and add as an option
    gid = conn.api_thread.gid.gid_val
    segments = TxTennaSegment.tx_to_segments(
        gid, str_hex_tx, str_hex_tx_hash, str(conn.messageIdx), network, False
    )
    for seg in segments:
        conn.send_broadcast(seg.serialize_to_json())
        sleep(10)
    conn.messageIdx = (conn.messageIdx + 1) % 9999
    wait_for(lambda: conn.events.callback.qsize() > evt_start_len)
    result = []
    while conn.events.callback.qsize() > evt_start_len:
        result.append(conn.events.callback.get())
    return {"mesh_broadcast_rawtx": result}
    


def rpc_getbalance(conn, rem):
    """
    Call local Bitcoin RPC method 'getbalance'

    Usage: rpc_getbalance
    """
    try:
        proxy = bitcoin.rpc.Proxy()
        balance = proxy.getbalance()
        print("getbalance: " + str(balance))
    except Exception:  # pylint: disable=broad-except
        traceback.print_exc()


def rpc_sendrawtransaction(conn, hex):
    """
    Call local Bitcoin RPC method 'sendrawtransaction'

    Usage: rpc_sendrawtransaction RAW_TX_HEX
    """
    try:
        proxy = bitcoin.rpc.Proxy()
        r = proxy.sendrawtransaction(hex)
        print("sendrawtransaction: " + str(r))
    except Exception:  # pylint: disable=broad-except
        traceback.print_exc()


def rpc_sendtoaddress(conn, rem):
    """
    Call local Bitcoin RPC method 'sendtoaddress'

    Usage: rpc_sendtoaddress ADDRESS SATS
    """
    try:
        proxy = bitcoin.rpc.Proxy()
        (addr, amount) = rem.split()
        r = proxy.sendtoaddress(addr, amount)
        print("sendtoaddress, transaction id: " + str(r["hex"]))
    except Exception:  # pylint: disable=broad-except
        traceback.print_exc()


def mesh_sendtoaddress(conn, rem):
    """ 
    Create a signed transaction and broadcast it over the connected mesh device. The transaction 
    spends some amount of satoshis to the specified address from the local bitcoind wallet and selected network. 

    Usage: mesh_sendtoaddress ADDRESS SATS NETWORK(m|t)

    eg. txTenna> mesh_sendtoaddress 2N4BtwKZBU3kXkWT7ZBEcQLQ451AuDWiau2 13371337 t
    """
    try:

        proxy = bitcoin.rpc.Proxy()
        (addr, sats, network) = rem.split()

        # Create the txout. This time we create the scriptPubKey from a Bitcoin
        # address.
        txout = CMutableTxOut(sats, CBitcoinAddress(addr).to_scriptPubKey())

        # Create the unsigned transaction.
        unfunded_transaction = CMutableTransaction([], [txout])
        funded_transaction = proxy.fundrawtransaction(unfunded_transaction)
        signed_transaction = proxy.signrawtransaction(funded_transaction["tx"])
        txhex = b2x(signed_transaction["tx"].serialize())
        txid = b2lx(signed_transaction["tx"].GetTxid())
        print(
            "sendtoaddress_mesh (tx, txid, network): " + txhex + ", " + txid,
            ", " + network,
        )

        # broadcast over mesh
        conn.mesh_broadcast_rawtx(txhex + " " + txid + " " + network)

    except Exception:  # pylint: disable=broad-except
        traceback.print_exc()

    try:
        # lock UTXOs used to fund the tx if broadcast successful
        vin_outpoints = set()
        for txin in funded_transaction["tx"].vin:
            vin_outpoints.add(txin.prevout)
        # json_outpoints = [{'txid':b2lx(outpoint.hash), 'vout':outpoint.n}
        #              for outpoint in vin_outpoints]
        # print(str(json_outpoints))
        proxy.lockunspent(False, vin_outpoints)

    except Exception:  # pylint: disable=broad-except
        # TODO: figure out why this is happening
        print("RPC timeout after calling lockunspent")


def broadcast_messages(conn, send_dir):
    """ 
    Watch a particular directory for files with message data to be broadcast over the mesh network

    Usage: broadcast_messages DIRECTORY

    eg. txTenna> broadcast_messages ./downloads
    """

    if send_dir is not None:
        # start new thread to watch directory
        conn.watch_dir_thread = Thread(target=conn.watch_messages, args=(send_dir,))
        conn.watch_dir_thread.start()


def watch_messages(conn, send_dir):
    before = {}
    while os.path.exists(send_dir):
        sleep(10)
        after = dict([(f, None) for f in os.listdir(send_dir)])
        new_files = [f for f in after if not f in before]
        if new_files:
            conn.broadcast_message_files(send_dir, new_files)
        before = after


def broadcast_message_files(conn, directory, filenames):
    for filename in filenames:
        print("Broadcasting ", directory + "/" + filename)
        f = open(directory + "/" + filename, "r")
        message_data = f.read()
        f.close()

        # binary to ascii encoding and strip out newlines
        encoded = zlib.compress(message_data, 9).encode("base64").replace("\n", "")
        print("[\n" + encoded.decode() + "\n]")

        gid = conn.api_thread.gid.gid_val
        segments = TxTennaSegment.tx_to_segments(
            gid, encoded, filename, str(conn.messageIdx), "d", False
        )
        for seg in segments:
            conn.send_broadcast(seg.serialize_to_json())
            sleep(10)
        conn.messageIdx = (conn.messageIdx + 1) % 9999
