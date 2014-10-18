import logging
import logging.config
import sys
import redis

import win

from channel import (ReliableChannel, OrderedRedisMessageCache,
                     RedisDeadMessageBackend)
# CONSTANTS
prompt_string = ">> "
start_row = 2
current_row = start_row
current_input = ""

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "syslog": {
            "class": "logging.handlers.SysLogHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "address": "/dev/log"
        },
    },
    "loggers": {
        "": {
            "level": "DEBUG",
            "handlers": ["syslog", ],
            "propagate": True
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["syslog", ],
    }
}

# SETUP

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__file__)

publish_to = 'tcp://localhost:5556'
subscribe_from = 'tcp://localhost:5557'

identity = sys.argv[1]
server_identity = sys.argv[2]

if len(sys.argv) > 4:
    publish_to = sys.argv[3]
    subscribe_from = sys.argv[4]


r = redis.StrictRedis(host='localhost', port=6379, db=0)
message_cache = OrderedRedisMessageCache(r,
                                         identity + "_sent2",
                                         identity + "_received3")

dead_backend = RedisDeadMessageBackend(r, identity + "_dead2")

channel = ReliableChannel(identity, publish_to, subscribe_from,
                          message_cache=message_cache,
                          dead_message_backend=dead_backend,
                          send_expiry=2 * 60 * 60,  # 2 hours
                          acknowledge_expiry=2 * 60 * 60)  # 2 hours

logger.info("Finished server connection setup")

chat_win = win.ChatWin(">> ")


def listen_for_server_updates(win):
    channel.receive()
    channel.synchronize()


def enter(win, current_input):
    logger.info("Sending message: {}".format(current_input))
    channel.send(server_identity, current_input)
    win.show_message("me: {}".format(current_input))


def received_message(message):
    chat_win.show_message(message['headers']['source'] + ": " + message['data'])

chat_win.add_event_listener("LOOP_RUN", listen_for_server_updates)
chat_win.add_event_listener("ENTER", enter)

channel.register_callback(received_message)

# EVENT LOOP
chat_win.run()
