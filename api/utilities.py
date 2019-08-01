import time


def handle_event(evt):
    return {
        '__str__': evt.__str__(),
        'event_type': evt.event_type,
        'message': evt.message,
        'status': evt.status,
        'device_details': evt.device_details,
        'disconnect_code': evt.disconnect_code,
        'disconnect_reason': evt.disconnect_reason,
        'group': evt.group,
        'device_paths': evt.device_paths
    }


def wait_for(success, timeout=20, interval=1):
    start_time = time.time()
    while not success() and time.time() < start_time + timeout:
        time.sleep(interval)
    if time.time() > start_time + timeout:
        raise ValueError("Error waiting for {}", success)