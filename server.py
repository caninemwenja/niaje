import argparse

from channel import ReliableChannel

publish_to = 'tcp://localhost:5556'
subscribe_to = 'tcp://localhost:5557'

client_identities = []

channel = None


def on_message(message):
    print "Received: {}".format(message)
    source = message['headers']['source']
    rest_of_the_message = message['data']

    for client in client_identities:
        if client != source:
            channel.send(client, rest_of_the_message,
                         extra_headers={"source": source})


def server(args):
    global channel, client_identities, publish_to, subscribe_to
    if args.publish_to:
        publish_to = args.publish_to

    if args.subscribe_to:
        subscribe_to = args.subscribe_to

    client_identities = args.client_identities

    channel = ReliableChannel(args.server_identity, publish_to, subscribe_to)
    channel.register_callback(on_message)

    while True:
        try:
            channel.receive()
            channel.synchronize()
        except KeyboardInterrupt:
            print "Bye!"
            break


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-p", "--publish_to",
                        help="location to publish messages")
    parser.add_argument("-s", "--subscribe_to",
                        help="location to subscribe messages")
    parser.add_argument("server_identity",
                        help="the identity of this server")
    parser.add_argument("client_identities", nargs="+",
                        help="list of client identities to coordinate")

    args = parser.parse_args()
    server(args)


if __name__ == "__main__":
    main()
