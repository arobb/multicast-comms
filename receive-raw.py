# Multicast client
# Adapted from: http://chaos.weblogs.us/archives/164
# http://stackoverflow.com/questions/15197569/any-small-program-to-receive-multicast-packets-on-specified-udp-port
# http://stackoverflow.com/questions/603852/multicast-in-python

import socket

ANY = "0.0.0.0"
MCAST_ADDR = "224.1.1.1"
MCAST_PORT = 5007

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
socket.inet_aton(MCAST_ADDR) + socket.inet_aton(ANY))

# setblocking(0) is equiv to settimeout(0.0) which means we poll the socket.
# But this will raise an error if recv() or send() can't immediately find or send data.
sock.setblocking(0)

while 1:
    try:
        data, addr = sock.recvfrom(1024)
    except socket.error as e:
        pass
    else:
        print "From: ", addr
        print "Data: ", data
