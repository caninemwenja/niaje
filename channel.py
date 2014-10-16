import zmq


class Channel(object):

    def __init__(self, publish_to, receive_from, server=False):
        self.context = zmq.Context()
        self.sender = self.context.socket(zmq.PUB)
        self.receiver = self.context.socket(zmq.SUB)
        self.server = server

        if self.server:
            self.sender.bind(publish_to)
            self.receiver.bind(receive_from)
            self.receiver.setsockopt(zmq.SUBSCRIBE, b"")
        else:
            self.sender.connect(publish_to)
            self.receiver.connect(receive_from)
            self.receiver.setsockopt(zmq.SUBSCRIBE, b"")

        self.callbacks = []

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def receive(self):
        try:
            message = self.receiver.recv_string(zmq.DONTWAIT)
            for callback in self.callbacks:
                callback(message)
        except zmq.Again:
            pass

    def send(self, message):
        self.sender.send_string(message)
