import curses
import zmq
import signal
import logging
import logging.config

from functools import wraps

# CONSTANTS
prompt_string = ">> "
start_row = 2
current_row = start_row

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


class TimeoutError(Exception):
    pass


def timeout(seconds=10, error_message="Timed Out!"):
    logger.info("Timing out in: {}".format(seconds))

    def decorator(func):
        def _handle_timeout(signum, frame):
            logger.info("Timed out!")
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                logger.info("Killing signal anyways.")
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator

# SERVER CONNECTION SETUP
context = zmq.Context()
sender = context.socket(zmq.PUB)
receiver = context.socket(zmq.SUB)

sender.connect('tcp://localhost:5556')
receiver.connect('tcp://localhost:5557')
receiver.setsockopt(zmq.SUBSCRIBE, b"")

logger.info("Finished server connection setup")

# UI SETUP
screen = curses.initscr()
screen.clear()

messages_win = curses.newwin(curses.LINES - 1, curses.COLS, 0, 0)
actual_win = messages_win.subwin(curses.LINES - 2, curses.COLS - 1, 1, 1)
actual_win.addstr(current_row, 2, "Welcome to Zero Curses Chat!")
current_row += 1

messages_win.box()

screen.addstr(curses.LINES - 1, 0, prompt_string)

screen.noutrefresh()
messages_win.noutrefresh()
curses.doupdate()

logger.info("Finished UI setup")


# REUSABLE OPERATIONS
def prompt():
    logger.info("Prompting")
    screen.move(curses.LINES - 1, len(prompt_string))
    screen.clrtoeol()
    screen.move(curses.LINES - 1, len(prompt_string))


def next_row():
    logger.info("Moving to next row")
    global current_row
    current_row += 1


def print_string(string):
    logger.info("Printing string: {}".format(string))
    actual_win.addstr(current_row, 2, string)
    actual_win.refresh()
    next_row()


@timeout(10)
def read_string():
    inp = screen.getstr()
    logger.info("Preread got {}".format(inp))
    while not inp:
        inp = screen.getstr()
        logger.info("Preread got {}".format(inp))

    logger.info("Preread got valid string: {}".format(inp))
    return inp


def clear():
    global current_row
    logger.info("Clearing messages")
    # stupid implementation of clear by overwriting everything with
    # a blank line
    empty_line = ""  # weirdly enough `" " * len` didnt work
    for i in range(0, curses.COLS - 4):
        empty_line += " "

    for row in range(2, curses.LINES - 4):
        actual_win.addstr(row, 2, empty_line)

    actual_win.refresh()
    current_row = start_row


def die():
    logger.info("Dying")
    signal.alarm(0)
    curses.endwin()


prompt()

# EVENT LOOP
while True:
    try:
        logger.info("Checking if there are any server messages")

        try:
            message = receiver.recv_string(zmq.DONTWAIT)
            print_string(message)
            logger.info("Message from server: {}".format(message))
        except zmq.Again:
            pass

        logger.info("Checking if there are any user messages")

        try:
            inp = read_string()

            if inp == "quit" or inp == "exit":
                break

            if inp == "clear" or current_row == curses.LINES - 3:
                clear()
                prompt()
                continue

            sender.send_string(inp)
            prompt()
            logger.info("Message from user: {}".format(inp))
        except TimeoutError:
            pass
    except KeyboardInterrupt:
        break
    except Exception:
        die()
        raise

die()
