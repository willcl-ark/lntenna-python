import queue
from lntenna.gotenna.utilities import handle_event, handle_text_msg


class Events:
    def __init__(self):
        self.msg = queue.LifoQueue()
        self.msg._name = "msg_events"
        self.device_present = queue.LifoQueue()
        self.device_present._name = "device_present_events"
        self.connect = queue.LifoQueue()
        self.connect._name = "connect_events"
        self.disconnect = queue.LifoQueue()
        self.disconnect._name = "disconnect_events"
        self.status = queue.LifoQueue()
        self.status._name = "status_events"
        self.group_create = queue.LifoQueue()
        self.group_create._name = "group_create_events"
        self.callback = queue.LifoQueue()
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

    def get_all_callback(self):
        """Returns a dict, where the first entry contains a list of callback messages
        received from newest to oldest"""
        msgs = []
        result = {self.callback._name: msgs}
        while not self.callback.empty():
            msgs.append((self.callback.get()))
        result[self.callback._name] = msgs
        return result

    def clear_all_messages(self):
        self.__init__()
