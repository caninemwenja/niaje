import curses

screen = curses.initscr()
screen.clear()
screen.border(0)

start_row = 2
end_row = 30
current_row = start_row
prompt_string = ">> "


def start_from_top():
    global current_row
    screen.clear()
    screen.border(0)
    current_row = start_row


def print_str(string, *args, **kwargs):
    screen.addstr(current_row, 2, string, *args, **kwargs)
    screen.refresh()


def get_input():
    inp = screen.getstr(current_row, len(prompt_string)+2)
    return inp


def next_row():
    global current_row
    current_row += 1


while True:
    try:
        if current_row == end_row:
            start_from_top()

        print_str(prompt_string)
        inp = get_input()

        if inp == "quit" or inp == "exit":
            break

        if inp == "clear":
            start_from_top()
            continue

        next_row()
        print_str(inp, curses.A_BOLD)
        next_row()
    except KeyboardInterrupt:
        break
    except curses.error:
        start_from_top()

curses.endwin()
