import Queue
from utilities import handle_event, handle_text_msg


class Events:
    def __init__(self):
        self.msg = Queue.LifoQueue()
        self.msg._name = "msg_events"
        self.device_present = Queue.LifoQueue()
        self.device_present._name = "device_present_events"
        self.connect = Queue.LifoQueue()
        self.connect._name = "connect_events"
        self.disconnect = Queue.LifoQueue()
        self.disconnect._name = "disconnect_events"
        self.status = Queue.LifoQueue()
        self.status._name = "status_events"
        self.group_create = Queue.LifoQueue()
        self.group_create._name = "group_create_events"
        self.callback = Queue.LifoQueue()
        self.callback._name = "callback_events"

    def get_all_connection(self):
        """Get all connect, disconnect and device present messages
        Returns a dict of queues, and their respective messages as a list for each queue
        """
        queues = [self.device_present, self.connect, self.disconnect]
        result = {}

        for queue in queues:
            lst = []
            while not queue.empty():
                lst.append(handle_event(queue.get()))
            result[queue._name] = lst

        return result

    def get_all_messages(self):
        """Returns a dict, where the first entry contains a list of messages received
        from newest to oldest"""
        msgs = []
        result = {self.msg._name: msgs}
        while not self.msg.empty():
            msgs.append(handle_text_msg(self.msg.get()))
        result[self.msg._name] = msgs
        return result
