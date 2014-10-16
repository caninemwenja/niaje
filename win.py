import curses
import curses.ascii
import logging

logger = logging.getLogger(__file__)


class ChatWin(object):
    start_row = 2
    event_types = ('ENTER', 'LOOP_RUN')

    def __init__(self, prompt_string):
        self.prompt_string = prompt_string
        self.current_row = self.start_row
        self.current_input = ""
        self.event_listeners = {}

        for event_type in self.event_types:
            self.event_listeners[event_type] = []

    def setup(self):
        self.screen = curses.initscr()
        self.screen.clear()
        self.messages_win = curses.newwin(curses.LINES - 1, curses.COLS, 0, 0)
        self.actual_win = self.messages_win.subwin(curses.LINES - 2, curses.COLS - 1, 1, 1)
        self.messages_win.box()
        self.screen.addstr(curses.LINES - 1, 0, self.prompt_string)
        self.screen.nodelay(True)
        curses.noecho()
        curses.cbreak()
        self.screen.keypad(1)

        self.screen.noutrefresh()
        self.messages_win.noutrefresh()
        curses.doupdate()

    def show_message(self, message):
        logger.debug("Showing message: {}".format(message))
        self.actual_win.addstr(self.current_row, 2, message)
        self.actual_win.refresh()
        self.current_row += 1

    def move_cursor_to_prompt(self):
        y = curses.LINES - 1
        x = len(self.prompt_string) + len(self.current_input)
        logger.debug("Moving cursor to x: {}, y: {}".format(x, y))
        self.screen.move(y, x)

    def show_prompt(self):
        logger.debug("Prompting: {}".format(self.prompt_string + self.current_input))
        self.move_cursor_to_prompt()
        self.screen.clrtoeol()
        if self.current_input != "":
            self.screen.addstr(curses.LINES - 1, len(self.prompt_string),
                               self.current_input)
            curses.doupdate()
        self.move_cursor_to_prompt()

    def clear(self):
        logger.debug("Clearing")
        # stupid implementation of clear by overwriting everything with
        # a blank line
        empty_line = ""  # weirdly enough `" " * len` didnt work
        for i in range(0, curses.COLS - 4):
            empty_line += " "

        for row in range(2, curses.LINES - 3):
            self.actual_win.addstr(row, 2, empty_line)

        self.actual_win.refresh()
        self.current_row = self.start_row

    def close(self):
        logger.debug("Closing ship")
        curses.nocbreak()
        self.screen.keypad(0)
        curses.echo()
        curses.endwin()

    def add_event_listener(self, event_type, callback):
        if event_type not in self.event_types:
            raise NotImplementedError()

        self.event_listeners[event_type].append(callback)

    def handle_user_input(self, character):
        logger.info("Received character: {}".format(character))
        is_enter = (character == curses.ascii.LF
                    or character == curses.ascii.CR
                    or character == curses.ascii.NL
                    or character == curses.KEY_ENTER)
        is_backspace = (character == curses.ascii.BS
                        or character == curses.ascii.DEL
                        or character == curses.KEY_BACKSPACE)
        if is_enter:
            logger.info("Received enter")
            if self.current_input == "quit" or self.current_input == "exit":
                logger.info("Quiting")
                raise KeyboardInterrupt()
            elif self.current_input == "clear":
                logger.info("Clearing")
                self.clear()
            else:
                for callback in self.event_listeners['ENTER']:
                    callback(self, self.current_input)

            self.current_input = ""
            logger.info("Emptied current input: {}".format(self.current_input))
        elif is_backspace:
            self.current_input = self.current_input[:-1]
        elif curses.ascii.isprint(character):
            self.current_input += curses.ascii.unctrl(character)

    def read_from_ui(self, callback):
        c = self.screen.getch()

        if c != curses.ERR:
            callback(c)

    def run(self):
        self.setup()
        self.show_message("Welcome to Zero Curses Chat!")
        self.show_prompt()

        # EVENT LOOP
        while True:
            try:
                if self.current_row == curses.LINES - 3:
                    self.clear()

                for callback in self.event_listeners['LOOP_RUN']:
                    callback(self)

                #logger.info("Checking if there are any user messages")
                self.read_from_ui(self.handle_user_input)
                self.show_prompt()
            except KeyboardInterrupt:
                break
            except Exception:
                self.close()
                raise

        self.close()
