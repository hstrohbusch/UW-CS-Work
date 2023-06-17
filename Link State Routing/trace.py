import argparse
from datetime import datetime
import socket
import struct
import sys

# INITIALIZE    

# parse arguments
parser = argparse.ArgumentParser()

parser.add_argument('-a', "--routetrace_port",required=True , type=int)        # port of this node
parser.add_argument('-b', "--source_hostname",required=True)               # name of topology file
parser.add_argument('-c', "--source_port",required=True , type=int)        # port of this node
parser.add_argument('-d', "--destination_hostname",required=True)
parser.add_argument('-e', "--destination_port",required=True , type=int)        # port of this node
parser.add_argument('-f', "--debug_option",required=True, type=int)      

args = parser.parse_args()

if(args.debug_option != 0 and args.debug_option !=1):
    print('invalid debug option, must be 0 or 1')
    exit(1)

# bind to socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)
hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname)

print(socket.gethostname())

try:
    sock.bind((HOST, args.routetrace_port))
except Exception as e: 
    print(e)
    exit(1)

HOST = socket.gethostbyname(hostname)
# print(HOST)
HOST = socket.inet_aton(HOST)
# print(HOST)
HOST = int.from_bytes(HOST, sys.byteorder)
# print(HOST)
HOST = socket.htonl(HOST)
# print(HOST)
# HOST = socket.htonl(HOST)

sourceIP = socket.gethostbyname(args.source_hostname)
source = (sourceIP, args.source_port)

destination = socket.gethostbyname(args.destination_hostname)
# print(destination)
destIP = destination
destination = socket.inet_aton(destination)
# print(destination)
destination = int.from_bytes(destination, sys.byteorder)
# print(destination)
destination = socket.htonl(destination)
# print(destination)
# destination = socket.htonl(destination)

finished = False
ttl = 0

sock.setblocking(1)

while not finished:
    rtHead = struct.pack("!cHIHIH", 'T'.encode(), socket.htons(ttl), HOST ,
                         socket.htons(args.routetrace_port), destination,
                         socket.htons(args.destination_port))
    
    if(args.debug_option):
        print('ttl: '+str(ttl)+'\tsource: '+str(sourceIP)+', '+str(args.source_port)+
              '\tdestination: '+ str(destIP)+', '+str(args.destination_port))
    
    sock.sendto(rtHead, source)

    response = sock.recv(360)

    packed_path = response[15:]
    path = []

    while packed_path:
        # packed_tup = packed_neighbors[:17] + packed_neighbors[15:17].ljust(4, b"\x00")
        packed_tup = packed_path[:17]
        pair = struct.unpack("!15sH", packed_tup)
        # node_neighbors.append((pair[0].decode().strip("\x00"), pair[1]))
        path.append( (pair[0].decode().strip("\x00"), socket.ntohs(pair[1]) ) )
        packed_path = packed_path[17:]

    if path[len(path)-1] == (destIP, args.destination_port):
        finished = True
        for i in range(len(path)):
            print(str(i)+' '+str(path[i][0])+', '+str(path[i][1]))
    elif path[len(path)-1] == ('err', 0):
        print('There is no route currently accessible to that node')
        finished = True
    else:
        ttl += 1 

sock.close()
exit(0)