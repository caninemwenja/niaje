import curses
import zmq

prompt_string = ">> "
start_row = 2
current_row = start_row

context = zmq.Context()
sender = context.socket(zmq.PUB)
receiver = context.socket(zmq.SUB)

sender.connect('tcp://localhost:5556')
receiver.connect('tcp://localhost:5557')
receiver.setsockopt(zmq.SUBSCRIBE, b"")

screen = curses.initscr()
screen.clear()

messages_win = curses.newwin(curses.LINES-1, curses.COLS, 0, 0)
actual_win = messages_win.subwin(curses.LINES-2, curses.COLS-1, 1, 1)
actual_win.addstr(current_row, 2, "me: Here's a message")
current_row += 1

messages_win.box()

screen.addstr(curses.LINES-1, 0, prompt_string)

screen.noutrefresh()
messages_win.noutrefresh()

curses.doupdate()

screen.move(curses.LINES-1, len(prompt_string))

while True:
    try:
        inp = screen.getstr()

        if current_row == curses.LINES-3 or inp == "clear":
            empty_line = ""
            for i in range(0, curses.COLS-2):
                empty_line += " "
            for row in range(2, curses.LINES-3):
                actual_win.addstr(row, 2, empty_line)
            actual_win.refresh()
            current_row = start_row
            screen.move(curses.LINES-1, len(prompt_string))
            screen.clrtoeol()
            screen.move(curses.LINES-1, len(prompt_string))
            continue

        if inp == "quit" or inp == "exit":
            break

        actual_win.addstr(current_row, 2, "me: "+inp)
        actual_win.refresh()

        current_row += 1

        screen.move(curses.LINES-1, len(prompt_string))
        screen.clrtoeol()
        screen.move(curses.LINES-1, len(prompt_string))
    except KeyboardInterrupt:
        break
    except Exception:
        curses.endwin()
        raise

curses.endwin()
