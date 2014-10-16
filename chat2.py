import logging
import logging.config

import channel
import win
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

channel = channel.Channel('tcp://localhost:5556', 'tcp://localhost:5557')
logger.info("Finished server connection setup")

chat_win = win.ChatWin(">> ")


def listen_for_server_updates(win):
    channel.receive()


def enter(win, current_input):
    logger.info("Sending message: {}".format(current_input))
    channel.send(current_input)


def received_message(message):
    chat_win.show_message(message)

chat_win.add_event_listener("LOOP_RUN", listen_for_server_updates)
chat_win.add_event_listener("ENTER", enter)

channel.add_callback(received_message)

# EVENT LOOP
chat_win.run()
