import ast
import time
import requests
import lntenna.api.config


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
        if lntenna.api.config.connection is None:
            return {
                "status": "Connection does not exist. First create connection using 'sdk_token'"
            }
        result = func(*args, **kwargs)
        return result

    return exists


def prepare_api_request(request):
    """Takes a dict of the form:
    {"type": "POST",
     "url": "www.xyz.com/api/v1.0/order",
     "params: {"param_1": "start_time=1"},
     "headers": {"header_1": "header"},
     "data": {"data_1": "some_data"},
     "json": {"json_data": {"json_stuff": "data"}}
     }

     Only working with GET or POST currently
    """
    req = requests.Request(request["type"])
    req.url = request["url"]
    req.headers = request["headers"] if "headers" in request else {}
    req.data = ast.literal_eval(request["data"]) if "data" in request else []
    req.params = ast.literal_eval(request["params"]) if "params" in request else {}
    req.json = ast.literal_eval(request["json"]) if "json" in request else {}
    prepped = req.prepare()
    return prepped


# def decimal_to_string(dict_obj):
#     for k, v in dict_obj.iteritems():
#         if isinstance(v, dict):
#             dict_obj[k] = decimal_to_string(v)
#         elif isinstance(v, decimal.Decimal):
#             dict_obj[k] = str(v)
#         else:
#             dict_obj[k] = v
#     return dict_obj
