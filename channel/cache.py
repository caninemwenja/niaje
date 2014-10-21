import json

from collections import OrderedDict


class MessageCache(object):

    def get_unconfirmed_messages(self):
        raise NotImplementedError()

    def get_received_syn_messages(self):
        raise NotImplementedError()

    def store_message_to_send(self, message_id, message):
        raise NotImplementedError()

    def confirm(self, message_id):
        raise NotImplementedError()

    def is_unconfirmed(self, message_id):
        raise NotImplementedError()

    def is_already_received(self, message_id):
        raise NotImplementedError()

    def mark_as_received(self, message_id, message):
        raise NotImplementedError()


class MemoryMessageCache(MessageCache):

    def __init__(self):
        self.sent = {}
        self.received = {}

    def get_unconfirmed_messages(self):
        return [message for message in self.sent.values()
                if message['status'] == 'SYN']

    def get_received_syn_messages(self):
        return [message for message in self.received.values()
                if message['status'] == 'SYN']

    def store_message_to_send(self, message_id, message):
        self.sent[message_id] = message

    def confirm(self, message_id):
        self.sent[message_id]['status'] = 'ACK'

    def is_unconfirmed(self, message_id):
        return message_id in self.sent and self.sent[message_id]['status'] == 'SYN'

    def is_already_received(self, message_id):
        return message_id in self.received

    def mark_as_received(self, message_id, message):
        self.received[message_id] = message


class OrderedMemoryMessageCache(MemoryMessageCache):

    def __init__(self):
        self.sent = OrderedDict()
        self.received = OrderedDict()


class RedisMessageCache(MessageCache):

    def __init__(self, redis_connection, sent_name, received_name):
        self.r = redis_connection
        self.sent_name = sent_name
        self.received_name = received_name

    def serialize(self, data):
        return json.dumps(data)

    def unserialize(self, data):
        return json.loads(data)

    def get_unconfirmed_messages(self):
        messages = [self.unserialize(message) for message in self.r.hvals(self.sent_name)]
        return [message for message in messages if message['status'] == 'SYN']

    def get_received_syn_messages(self):
        messages = [self.unserialize(message) for message in self.r.hvals(self.received_name)]
        return [message for message in messages if message['status'] == 'SYN']

    def store_message_to_send(self, message_id, message):
        self.r.hset(self.sent_name, message_id, self.serialize(message))

    def confirm(self, message_id):
        message = self.unserialize(self.r.hget(self.sent_name, message_id))
        message['status'] = 'ACK'
        self.r.hset(self.sent_name, message_id, self.serialize(message))

    def is_unconfirmed(self, message_id):
        return self.r.hexists(self.sent_name, message_id) and self.unserialize(self.r.hget(self.sent_name, message_id))['status'] == 'SYN'

    def is_already_received(self, message_id):
        return self.r.hexists(self.received_name, message_id)

    def mark_as_received(self, message_id, message):
        self.r.hset(self.received_name, message_id, self.serialize(message))


class OrderedRedisMessageCache(RedisMessageCache):

    def get_unconfirmed_messages(self):
        key_list = self.sent_name + "_keys"
        message_ids = self.r.lrange(key_list, 0, self.r.llen(key_list))

        if not message_ids:
            return []

        messages = [self.unserialize(message) for message in self.r.hmget(self.sent_name, *message_ids) if message]
        return [message for message in messages if message['status'] == 'SYN']

    def get_received_syn_messages(self):
        key_list = self.received_name + "_keys"
        message_ids = self.r.lrange(key_list, 0, self.r.llen(key_list))

        if not message_ids:
            return []

        messages = [self.unserialize(message) for message in self.r.hmget(self.received_name, *message_ids) if message]
        return [message for message in messages if message['status'] == 'SYN']

    def store_message_to_send(self, message_id, message):
        key_list = self.sent_name + "_keys"
        self.r.rpush(key_list, message_id)

        super(OrderedRedisMessageCache, self).store_message_to_send(message_id, message)

    def confirm(self, message_id):
        super(OrderedRedisMessageCache, self).confirm(message_id)
        key_list = self.sent_name + "_keys"
        self.r.lrem(key_list, 0, message_id)

    def mark_as_received(self, message_id, message):
        key_list = self.received_name + "_keys"

        if not self.is_already_received(message_id):
            self.r.rpush(key_list, message_id)

        if message['status'] == 'ACK':
            self.r.lrem(key_list, 0, message_id)

        super(OrderedRedisMessageCache, self).mark_as_received(message_id, message)
