import zmq
import sys

sub_port = 5556
pub_port = 5557

if len(sys.argv) > 2:
    sub_port = sys.argv[1]
    pub_port = sys.argv[2]

subscribe_to = "tcp://*:{}".format(sub_port)
publish_to = "tcp://*:{}".format(pub_port)

try:
    context = zmq.Context()
    frontend = context.socket(zmq.SUB)
    frontend.bind(subscribe_to)
    frontend.setsockopt(zmq.SUBSCRIBE, "")

    backend = context.socket(zmq.PUB)
    backend.bind(publish_to)

    zmq.device(zmq.FORWARDER, frontend, backend)
except KeyboardInterrupt:
    print "Bye!"
except Exception:
    print "Bringing down FORWARDER"
    raise
finally:
    frontend.close()
    backend.close()
    context.term()
