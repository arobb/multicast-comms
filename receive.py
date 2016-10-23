#!/usr/bin/env python
# Multicast client
# Adapted from: http://chaos.weblogs.us/archives/164
# http://stackoverflow.com/questions/15197569/any-small-program-to-receive-multicast-packets-on-specified-udp-port
# http://stackoverflow.com/questions/603852/multicast-in-python

from __future__ import print_function
import socket
import re
import hashlib
import time
import collections
import argparse, ConfigParser, inspect
import sys

dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# Function to allow printing to stderr
# http://stackoverflow.com/questions/5574702/how-to-print-to-stderr-in-python
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


parser = argparse.ArgumentParser(usage='%(prog)s [options]', description='Broadcast data to multicast audience.')
parser.add_argument('-c', '--config-file', required=False, default=dir+'/config.ini', nargs='?', dest='config', help='Path to config file')
parser.add_argument('-g', '--multicast-group', required=False, nargs='?', dest='group', help='Multicast group/address')
parser.add_argument('-k', '--shared-key', required=False, nargs='?', dest='key', help='Shared key. Overrides key from config file')
parser.add_argument('-p', '--multicast-port', required=False, nargs='?', dest='port', help='UDP port to use')
parser.add_argument('-v', '--debug', required=False, action='store_true', dest='debug', help='Debug mode')
args, unk = parser.parse_known_args()

config = ConfigParser.SafeConfigParser()
config.read(args.config)


ANY = "0.0.0.0"
DEBUG = args.debug
MCAST_GRP = config.get('Network', 'multicast_group') if args.group is None else args.group
MCAST_PORT = config.getint('Network', 'multicast_port') if args.port is None else int(args.port)
SHARED_KEY = config.get('Security', 'shared_key', 1) if args.key is None else args.key


# Replay attack protection
# Check the last 1,000 validated messages to ensure
# that we don't process a re-transmitted message
REPLAY_LIST = collections.deque([], 1000)
replay_attempts = 0


# Validate the message we received was generated by a trusted source
def validate_digest(givendigest, entropy, counter, data):
    newdigest = hashlib.sha256( \
      SHARED_KEY \
      +str(entropy) \
      +str(counter) \
      +str(data) \
      ).hexdigest()

    return (givendigest == newdigest)


# Validate the message we received was not retransmitted
# True is good, means no replay found
# Don't add the new info here to REPLAY_LIST
def check_replay(entropy, counter):
    for val in REPLAY_LIST:
        if val == str(entropy)+str(counter):
            return False

    return True


# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

# Allow multiple sockets to use the same PORT number
sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

# Bind to the port that we know will receive multicast data
sock.bind((ANY,MCAST_PORT))

# Tell the kernel that we want to add ourselves to a multicast group
# The address for the multicast group is the third param
status = sock.setsockopt(socket.IPPROTO_IP,
socket.IP_ADD_MEMBERSHIP,
socket.inet_aton(MCAST_GRP) + socket.inet_aton(ANY))

# setblocking(0) is equiv to settimeout(0.0) which means we poll the socket.
# But this will raise an error if recv() or send() can't immediately find or send data.
sock.setblocking(0)

while 1:
    try:
        time.sleep(1)
        data, addr = sock.recvfrom(1024)
    except socket.error as e:
        pass
    else:
        # Extract components of a message
        match = re.search('^([a-zA-Z0-9]*)\n([a-zA-Z0-9]*)\n([0-9]*)\n(.*)', data, re.DOTALL)

        if match.lastindex == None:
            pass
        else:
            digest = match.group(1)
            entropy = match.group(2)
            counter = match.group(3)
            data = match.group(4)
            hashvalid = validate_digest(digest, entropy, counter, data)
            noreplay = check_replay(entropy, counter)

            if DEBUG:
                eprint("From: ", addr)
                eprint("Num matches: ", match.lastindex)
                eprint("Digest: ", digest)
                eprint("Entropy: ", entropy)
                eprint("Transmission counter: ", counter)
                eprint("Valid digest: ", "Yes" if hashvalid else "No")
                eprint("Not replayed: ", "Yes" if noreplay else "No")
                eprint("Data: ", str(data))

            if not hashvalid or not noreplay:
                #eprint("Bad transmission")

                if not noreplay:
                    replay_attempts = replay_attempts+1
            else:
                # Add the 'replay' info to the list here; now we know
                # the basic information is valid (don't do it before validating
                # the digest so no one can poison the validation, and don't do
                # it before checking for a replay so we don't re-add the same
                # information multiple times)
                REPLAY_LIST.append(str(entropy)+str(counter))

                #print("Good transmission")
                print("### Start message " + str(entropy) + str(counter) + " ###")
                print(str(data))
                print("### End message " + str(entropy) + str(counter) + " ###")
