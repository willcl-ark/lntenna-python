import time
import config


MSG_TYPE = {2: "BROADCAST", 3: "EMERGENCY", 1: "GROUP", 0: "PRIVATE"}


def handle_event(evt):
    return {
        "__str__": evt.__str__(),
        "event_type": evt.event_type,
        "message": evt.message,
        "status": evt.status,
        "device_details": evt.device_details,
        "disconnect_code": evt.disconnect_code,
        "disconnect_reason": evt.disconnect_reason,
        "group": evt.group,
        "device_paths": evt.device_paths,
    }


def handle_text_msg(message):
    msg = message
    payload = {
        "message": msg.message.payload.message,
        "sender": {
            "gid": msg.message.payload.sender.gid_val,
            "gid_type": msg.message.payload.sender.gid_type,
        },
        "time_sent": str(msg.message.payload.time_sent),
        "counter": msg.message.payload.counter,
        "sender_initials": msg.message.payload.sender_initials,
    }
    destination = {
        "gid_type": msg.message.destination.gid_type,
        "gid_val": msg.message.destination.gid_val,
        "type": MSG_TYPE[msg.message.destination.gid_type],
    }

    return {
        "message": {
            "destination": destination,
            "max_hops": msg.message.max_hops,
            "payload": payload,
        }
    }


def wait_for(success, timeout=20, interval=1):
    start_time = time.time()
    while not success() and time.time() < start_time + timeout:
        time.sleep(interval)
    if time.time() > start_time + timeout:
        raise ValueError("Error waiting for {}", success)


def check_connection(func):
    def exists(*args, **kwargs):
        if config.connection is None:
            return {
                "status": "Connection does not exist. First create connection using 'sdk_token'"
            }
        result = func(*args, **kwargs)
        return result

    return exists
