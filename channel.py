import zmq
import json
import uuid
import time


class Channel(object):

    def __init__(self, identity, publish_to, receive_from):
        self.identity = identity
        self.context = zmq.Context()
        self.sender = self.context.socket(zmq.PUB)
        self.receiver = self.context.socket(zmq.SUB)

        self.sender.connect(publish_to)
        self.receiver.connect(receive_from)
        subscription = identity + "::"
        subscription = subscription.encode("ascii")
        self.receiver.setsockopt(zmq.SUBSCRIBE, subscription)

        self.callbacks = []

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def pre_callback(self, message):
        # strip the identity
        return message[len(self.identity) + 2:]  # +2 for ::

    def receive(self):
        try:
            message = self.receiver.recv_string(zmq.DONTWAIT)
            for callback in self.callbacks:
                message = self.pre_callback(message)
                if message:
                    callback(message)
        except zmq.Again:
            pass

    def send(self, destination, message):
        actual = "{}::{}".format(destination, message)
        self.sender.send_string(actual)


class JsonChannel(Channel):

    def __init__(self, *args, **kwargs):
        super(JsonChannel, self).__init__(*args, **kwargs)

        self.default_headers = {
            'source': self.identity
        }

        if 'default_headers' in kwargs:
            self.default_headers.update(kwargs['default_headers'])

    def send(self, destination, message_data, extra_headers=None):
        headers = {
            "destination": destination,
        }

        if self.default_headers:
            headers.update(self.default_headers)

        if extra_headers:
            headers.update(extra_headers)

        actual_message = {
            "headers": headers,
            "data": message_data
        }

        super(JsonChannel, self).send(destination, json.dumps(actual_message))

    def pre_callback(self, message):
        message = super(JsonChannel, self).pre_callback(message)
        return json.loads(message)


class ReliableChannel(JsonChannel):

    def __init__(self, *args, **kwargs):
        super(ReliableChannel, self).__init__(*args, **kwargs)

        self.current_message_id = self.generate_new_message_id()
        self.received = {}
        self.sent = {}

    def get_current_id(self):
        return self.identity + ":::" + str(self.current_message_id)

    def generate_new_message_id(self):
        return (str(time.time()) + str(uuid.uuid4()))

    def synchronize(self):
        # resend unconfirmed messages
        for message in self.sent.values():
            if message['status'] == 'SYN':
                super(ReliableChannel, self).send(message['destination'],
                                                  message['message'],
                                                  message['headers'])

        # confirm received messages
        for message in self.received.values():
            if message['status'] == 'SYN':
                message['message']['headers'].update({'type': 'ACK'})
                super(ReliableChannel, self).send(message['destination'],
                                                  message['message']['data'],
                                                  message['message']['headers'])

    def send(self, destination, message_data, extra_headers=None):
        headers = {
            'message_id': self.get_current_id()
        }

        if extra_headers:
            headers.update(extra_headers)

        self.sent[self.get_current_id()] = {
            'message': message_data,
            'destination': destination,
            'headers': headers,
            'status': 'SYN',
        }

        self.current_message_id = self.generate_new_message_id()

    def pre_callback(self, message):
        message = super(ReliableChannel, self).pre_callback(message)

        message_id = message['headers']['message_id']

        if 'type' in message['headers'] and message['headers']['type'] == 'ACK':
            if message_id in self.sent:
                self.sent[message_id]['status'] = 'ACK'

            return None

        if message_id in self.received:
            return None

        self.received[message_id] = {
            'message': message,
            'destination': message['headers']['source'],
            'status': 'SYN'
        }

        return message
