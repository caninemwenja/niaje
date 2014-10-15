import zmq

context = zmq.Context()
sender = context.socket(zmq.PUB)
receiver = context.socket(zmq.SUB)

sender.bind("tcp://*:5557")
receiver.bind("tcp://*:5556")

receiver.setsockopt(zmq.SUBSCRIBE, b"")

poller = zmq.Poller()
poller.register(receiver, zmq.POLLIN)

while True:
    try:
        socks = dict(poller.poll())

        if socks.get(receiver) == zmq.POLLIN:
            message = receiver.recv_string()
            sender.send_string(message)

            print "Received: {}".format(message)
    except KeyboardInterrupt:
        print "Bye!"
        break
