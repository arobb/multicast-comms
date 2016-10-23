#!/usr/bin/env python
# Multicast client
# Adapted from: http://chaos.weblogs.us/archives/164
# http://stackoverflow.com/questions/15197569/any-small-program-to-receive-multicast-packets-on-specified-udp-port
# http://stackoverflow.com/questions/603852/multicast-in-python

import socket
import argparse, ConfigParser, inspect, os

dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

parser = argparse.ArgumentParser(usage='%(prog)s [options]', description='Broadcast data to multicast audience.')
parser.add_argument('-c', '--config-file', required=False, default=dir+'/config.ini', nargs='?', dest='config', help='Path to config file')
parser.add_argument('-g', '--multicast-group', required=False, nargs='?', dest='group', help='Multicast group/address')
parser.add_argument('-k', '--shared-key', required=False, nargs='?', dest='key', help='Shared key. Overrides key from config file')
parser.add_argument('-p', '--multicast-port', required=False, nargs='?', dest='port', help='UDP port to use')
args, unk = parser.parse_known_args()

config = ConfigParser.SafeConfigParser()
config.read(args.config)

ANY = "0.0.0.0"
MCAST_GRP = config.get('Network', 'multicast_group') if args.group is None else args.group
MCAST_PORT = config.getint('Network', 'multicast_port') if args.port is None else int(args.port)

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
        data, addr = sock.recvfrom(10240)
    except socket.error as e:
        pass
    else:
        print "From: ", addr
        print "Data: ", data
