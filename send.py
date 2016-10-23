#!/usr/bin/env python
# http://stackoverflow.com/questions/603852/multicast-in-python

import socket
import argparse, ConfigParser, fileinput, inspect
import os, hashlib
from binascii import b2a_hex

dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# Generate random data for this use of the transmission library
RUNTIME_ENTROPY = b2a_hex(os.urandom(32))[0:32]

# For each transmission, increment the counter to help avoid
# replay attacks
TRANSMISSION_COUNTER = 0


parser = argparse.ArgumentParser(usage='%(prog)s [options]', description='Broadcast data to multicast audience.')
parser.add_argument('-c', '--config-file', required=False, default=dir+'/config.ini', nargs='?', dest='config', help='Path to config file')
parser.add_argument('-d', '--data', required=False, nargs='?', dest='data', help='Data to send. If empty uses stdin')
parser.add_argument('-g', '--multicast-group', required=False, nargs='?', dest='group', help='Multicast group/address')
parser.add_argument('-k', '--shared-key', required=False, nargs='?', dest='key', help='Shared key. Overrides key from config file')
parser.add_argument('-p', '--multicast-port', required=False, nargs='?', dest='port', help='UDP port to use')
parser.add_argument('-v', '--debug', required=False, action='store_true', dest='debug', help='Debug mode')
args, unk = parser.parse_known_args()

config = ConfigParser.SafeConfigParser()
config.read(args.config)

DEBUG = args.debug
MCAST_GRP = config.get('Network', 'multicast_group') if args.group is None else args.group
MCAST_PORT = config.getint('Network', 'multicast_port') if args.port is None else int(args.port)
SHARED_KEY = config.get('Security', 'shared_key', 1) if args.key is None else args.key


# Make sure the default was changed
if SHARED_KEY == "abc123":
    print "Please change the default key. No transmission was made. Exiting."
    exit(1)


# Read data
#data = "robot"
if args.data is None:
    data = ""
    for line in fileinput.input(unk):
        data += line
else:
    data = args.data


# Generate the message digest
# The digest is a hash of the shared key, entropy, counter, and data
# This can easily be recreated by a receiver to validate that the
# transmission was (1) created and (2) sent by a trusted source
hashfunc = hashlib.sha256()
hashfunc.update(str(SHARED_KEY))
hashfunc.update(str(RUNTIME_ENTROPY))
hashfunc.update(str(TRANSMISSION_COUNTER))
hashfunc.update(data)
digest = hashfunc.hexdigest()


# Combine the entropy, counter, and data into a package to send
envelope = "\n".join( \
  (str(digest) \
  , str(RUNTIME_ENTROPY) \
  , str(TRANSMISSION_COUNTER) \
  , str(data)))


# Open the transmission connection
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

# Perform the transmission
sock.sendto(envelope, (MCAST_GRP, MCAST_PORT))
TRANSMISSION_COUNTER=TRANSMISSION_COUNTER+1
