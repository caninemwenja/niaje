import curses
import zmq
import threading

context = zmq.Context()
sender = context.socket(zmq.PUB)
receiver = context.socket(zmq.SUB)

sender.connect('tcp://localhost:5556')
receiver.connect('tcp://localhost:5557')
receiver.setsockopt(zmq.SUBSCRIBE, b"")

#poller = zmq.Poller()
#poller.register(receiver, zmq.POLLIN)

screen = curses.initscr()
screen.clear()
screen.border(0)

start_row = 2
end_row = 30
current_row = start_row
prompt_string = ">> "

lock = threading.RLock()

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


def listener():
    while True:
        message = receiver.recv_string()
        lock.acquire()
        try:
            print_str(message, curses.A_BOLD)
            next_row()
        finally:
            lock.release()

t = threading.Thread(target=listener)
t.start()

while True:
    try:
        if current_row == end_row:
            lock.acquire()
            try:
                start_from_top()
            finally:
                lock.release()

        #while True:
        #    try:
        #        message = receiver.recv_string(zmq.DONTWAIT)
        #        print_str(message, curses.A_STANDOUT)
        #        next_row()
        #    except zmq.Again:
        #        break
        #socks = dict(poller.poll())

        #if socks.get(receiver) == zmq.POLLIN:
        #    message = receiver.recv_string()
        #    print_str(message, curses.A_STANDOUT)
        #    next_row()

        lock.acquire()
        try:
            print_str(prompt_string)
        finally:
            lock.release()

        inp = get_input()
        if inp == "quit" or inp == "exit":
            break

        if inp == "clear":
            lock.acquire()
            try:
                start_from_top()
            finally:
                lock.release()
            continue

        lock.acquire()
        try:
            sender.send_string(inp.decode('ascii'))
            next_row()
            print_str(inp, curses.A_BOLD)
            next_row()
        finally:
            lock.release()
    except KeyboardInterrupt:
        break
    except curses.error:
        lock.acquire()
        try:
            start_from_top()
        finally:
            lock.release()

curses.endwin()
