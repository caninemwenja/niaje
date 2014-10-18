import json


class DeadMessageBackend(object):

    def store(context, comment):
        return NotImplementedError()


class MemoryDeadMessageBackend(object):

    def __init__(self):
        self.message_store = {}

    def store(self, context, data, comment):
        details = {
            "comment": comment,
            "context": context,
            "data": data
        }
        self.message_store[context] = details


class RedisDeadMessageBackend(object):

    def __init__(self, redis_connection, store_name):
        self.r = redis_connection
        self.store_name = store_name

    def store(self, context, data, comment):
        details = {
            "comment": comment,
            "context": context,
            "data": data
        }
        self.r.hset(self.store_name, context, json.dumps(details))
