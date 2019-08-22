import threading
import types
from time import sleep, time

import requests
import simplejson as json

from lntenna.database import init as init_db, mesh_get_payment_hash, query_swap_details
from lntenna.gotenna.utilities import de_segment, prepare_api_request
from lntenna.swap import (
    auto_swap_complete,
    auto_swap_create,
    auto_swap_verify_preimage,
    auto_swap_verify_quote,
    monitor_swap_status,
    check_swap,
)

MSG_CODES = [
    "api_request",
    "sat_req",
    "sat_fill",
    "swap_tx",
    "swap_complete",
    "swap_check",
]


def handle_message(conn, message):
    """
    Handle messages received over the mesh network
    :param conn: the lntenna.gotenna.Connection instance
    :param message: as strings
    :return: result of message handling
    """

    payload = message.payload.message

    # test for jumbo:
    jumbo = True if payload.startswith("sm/") else False
    if jumbo:
        handle_jumbo_message(conn, message)
        return

    # handle a known message type defined in MSG_CODES
    try:
        # decode json-encoded strings
        payload = json.loads(payload)
        for k, v in payload.items():
            if k in MSG_CODES:
                conn.log(f"Handling a {k} message")
                # make sure all db tables needed exist
                # TODO: move this to more appropriate place
                init_db()
                # pass the full request dict through to parse message type later
                return handle_known_msg(conn, payload)
            else:
                conn.log(
                    f"Received json-encoded message but could not automatically "
                    f"handle:\n{payload}"
                    f"Not a known message type."
                )
    except json.JSONDecodeError:
        conn.log(f"Nothing to handle for non json-encoded message: \n{payload}")
    except Exception as e:
        conn.log(
            f"Raised exception when trying to handle message:\n"
            f"Payload: {payload}\n"
            f"{e}"
        )


def handle_known_msg(conn, message):
    for k, v in message.items():

        if k == "api_request":
            conn.log("Processing a api_request message")
            # pass the request dict only through
            prepped = prepare_api_request(v)
            conn.log("Prepared an api request")
            with requests.Session() as s:
                return s.send(prepped, timeout=30)

        if k == "sat_req":
            # do an automatic blocksat and swap setup
            conn.log("Processing a sat_req message")
            sat_fill = auto_swap_create(v, conn.cli)
            conn.send_jumbo(json.dumps(sat_fill))

        if k == "sat_fill":
            conn.log("Processing a sat_fill message")
            conn.log("Received a quote response")
            if conn.cli:
                swap_tx = auto_swap_verify_quote(v, conn.cli)
            else:
                swap_tx = auto_swap_verify_quote(v)
            conn.send_jumbo(json.dumps(swap_tx))

        if k == "swap_tx":
            conn.log("Processing a swap_tx message")
            swap_complete = auto_swap_complete(v["uuid"], v["tx_hex"], conn.cli, conn)
            conn.send_broadcast(json.dumps(swap_complete))

        if k == "swap_complete":
            conn.log("Processing a swap_complete message")
            try:
                # msg = json.loads(v)
                payment_hash = mesh_get_payment_hash(v["uuid"])
                if auto_swap_verify_preimage(
                    v["uuid"], v["preimage"], payment_hash, conn.cli
                ):
                    conn.log(v)
            except Exception:
                conn.log(v)

        if k == "swap_check":
            conn.log("Processing a swap_check message")
            # TODO: if we retrieve tx here we could query bitcoind to see if
            #   mainnet tx has at least 3 confirmations to minimise SSS
            #   calls
            # Lookup the relevant details from the db
            network, invoice, redeem_script = query_swap_details(v["uuid"])
            if network and invoice and redeem_script:
                conn.log(f"Successfully looked up details for swap_check")
            else:
                conn.send_broadcast(
                    f"swap_check for uuid: {v['uuid']} could not find "
                    f"order details for lookup in database"
                )
                return

            # Check the status and return it initially as a first response
            swap_status = check_swap(v["uuid"])
            if "payment_secret" in swap_status["response"]:
                conn.send_broadcast(
                    f"Swap complete. Preimage: "
                    f"{swap_status['response']['payment_secret']}"
                )
                return
            else:
                conn.send_broadcast(f"Swap incomplete: {swap_status['response']}")

            # If not complete, start a thread to monitor status intermittently or
            # intelligently based on SSS required confs for mainnet
            monitor_status = threading.Thread(
                target=monitor_sss, args=[v["uuid"], conn, 30, 1200]
            )
            monitor_status.start()


def handle_jumbo_message(conn, message):
    payload = message.payload.message
    # TODO: this cuts out all sender and receiver info -- ADD SENDER GID
    conn.log(f"Received jumbo message fragment")
    prefix, seq, length, msg = payload.split("/")
    if conn.jumbo_thread.is_alive():
        pass
    else:
        # start the jumbo monitor thread
        conn.events.jumbo_len = length
        conn.jumbo_thread = None
        conn.jumbo_thread = threading.Thread(
            target=monitor_jumbo_msgs, daemon=True, args=[conn]
        )
        conn.jumbo_thread.start()
    conn.events.jumbo.append(payload)
    return


def monitor_jumbo_msgs(conn, timeout=30):
    conn.log("Starting jumbo message monitor thread")
    start = time()
    missing = True
    while True and time() < start + timeout:
        conn.log(
            f"received: {len(conn.events.jumbo)} of {conn.events.jumbo_len} "
            f"jumbo messages"
        )
        if (
            len(conn.events.jumbo) == int(conn.events.jumbo_len)
            and len(conn.events.jumbo) is not 0
        ):
            missing = False
            # give handle_message the attributes it expects
            jumbo_message = types.SimpleNamespace()
            jumbo_message.payload = types.SimpleNamespace()
            # reconstruct the jumbo message
            jumbo_message.payload.message = de_segment(conn.events.jumbo)
            # send it back through handle_message
            conn.log(f"Jumbo message payload reconstituted")
            handle_message(conn, jumbo_message)
            break
        sleep(5)
    # reset jumbo events after timeout
    conn.events.init_jumbo()
    if missing:
        conn.log(
            "Did not receive all jumbo messages require for re-assembly. "
            "Please request the message again from the remote host."
        )
    return


def monitor_sss(uuid, conn, interval=30, timeout=1200):
    status = monitor_swap_status(uuid, conn.cli, interval, timeout, conn)
    conn.send_broadcast(json.dumps(status))
