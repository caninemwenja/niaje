import zmq
import argparse


def setup(location=None, server=False):
    context = zmq.Context()
    sender = context.socket(zmq.PUB)
    receiver = context.socket(zmq.SUB)

    if server:
        sender.bind('tcp://{}'.format(location[0]))
        receiver.bind('tcp://{}'.format(location[1]))
    else:
        sender.connect('tcp://{}'.format(location[0]))
        receiver.connect('tcp://{}'.format(location[1]))

    return sender, receiver


def start(args):
    sender, receiver = setup((args.publish, args.subscribe), args.server)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', action='store_true',
                        help='whether this node is a server or a client')
    parser.add_argument('publish', help='location to publish to')
    parser.add_argument('subscribe', help='location to subscribe from')

    parser.set_defaults(func=start)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
