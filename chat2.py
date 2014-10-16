import curses
import curses.ascii
import zmq
import logging
import logging.config

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

screen.nodelay(True)
curses.noecho()
curses.cbreak()
screen.keypad(1)

screen.noutrefresh()
messages_win.noutrefresh()
curses.doupdate()

logger.info("Finished UI setup")


# REUSABLE OPERATIONS
def prompt():
    logger.info("Prompting {}".format(current_input))
    screen.move(curses.LINES - 1, len(prompt_string) + len(current_input))
    if current_input != "":
        screen.addstr(curses.LINES - 1, len(prompt_string), current_input)
        curses.doupdate()
    else:
        screen.clrtoeol()
    screen.move(curses.LINES - 1, len(prompt_string) + len(current_input))


def next_row():
    logger.info("Moving to next row")
    global current_row
    current_row += 1


def print_string(string):
    logger.info("Printing string: {}".format(string))
    actual_win.addstr(current_row, 2, string)
    actual_win.refresh()
    next_row()


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
    curses.nocbreak()
    screen.keypad(0)
    curses.echo()
    curses.endwin()


def server_message(message):
    print_string(message)
    logger.info("Message from server: {}".format(message))


def read_from_server(callback):
    try:
        message = receiver.recv_string(zmq.DONTWAIT)
        callback(message)
    except zmq.Again:
        pass


def handle_user_input(character):
    global current_input
    logger.info("Received character: {}".format(character))
    is_enter = (character == curses.ascii.LF
                or character == curses.ascii.CR
                or character == curses.ascii.NL)
    is_backspace = (character == curses.ascii.BS
                    or character == curses.ascii.DEL)
    if is_enter:
        logger.info("Received enter")
        if current_input == "quit" or current_input == "exit":
            logger.info("Quiting")
            raise KeyboardInterrupt()
        elif current_input == "clear" or current_row == curses.LINES - 3:
            logger.info("Clearing")
            clear()
        else:
            logger.info("Sending message")
            sender.send_string(current_input)
            logger.info("Message from user: {}".format(current_input))

        current_input = ""
        logger.info("Emptied current input: {}".format(current_input))
    elif is_backspace:
        current_input = current_input[:-1]
    elif curses.ascii.isprint(character):
        current_input += curses.ascii.unctrl(character)


def read_from_ui(callback):
    c = screen.getch()

    if c != curses.ERR:
        callback(c)


prompt()

# EVENT LOOP
while True:
    try:
        logger.info("Checking if there are any server messages")
        read_from_server(server_message)

        logger.info("Checking if there are any user messages")
        read_from_ui(handle_user_input)

        prompt()
    except KeyboardInterrupt:
        break
    except Exception:
        die()
        raise

die()
