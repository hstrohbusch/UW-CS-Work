import argparse
from datetime import datetime
import socket
import struct
import sys

# INITIALIZE    

# parse arguments
parser = argparse.ArgumentParser()

parser.add_argument('-p', "--port",required=True , type=int)        # port of this node
parser.add_argument('-f', "--filename",required=True)               # name of topology file

args = parser.parse_args()

# bind to socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)
hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname)

try:
    sock.bind((HOST, args.port))
except Exception as e: 
    print(e)
    exit(1)

# global lists
neighbors = {}
nodeSeqNum = {}
topology = {}
forwardingTable = {}

# this node
SELF = (str(HOST), args.port)
# print(SELF)
#SELF = ('1.0.0.0', 1)

# global vars
ogNodeCount = 0
mySeqNum = 0
hello_rate = 0.25
lsm_rate = 0.25
last_hello = datetime.now()
last_lsm = datetime.now()

# reads the topology file with the name given in args and returns
# a dict with the structure node: [neighbors]
def readtopology():
    global topology
    with open(args.filename, 'r') as reader:
        line = reader.readlines()
        for l in line:
            pair = l.split()
            temp = pair[0].split(',')
            node = (temp[0], int(temp[1]))

            neighbors = []
            for e in range(1, len(pair)):
                n = pair[e].split(',')
                neighbors.append((n[0], int(n[1])))

            topology[node] = neighbors

    global ogNodeCount
    ogNodeCount = len(topology)
                
# this method is run constantly after initialization. It listens to incoming
# packets to decide and updates the topology and forwarding tables if it is 
# needed. It also sends them to forwardpacket for forwarding purposes.
def createroutes():
    # lists
    global neighbors
    global nodeSeqNum 
    global topology
    # vars
    global mySeqNum
    global hello_rate
    global lsm_rate
    global last_hello
    global last_lsm

    # Handle packets if they are ready
    try:
        packet = sock.recv(5146) # max request size        

        ptype = packet[:1]
        ptype = struct.unpack("!c",ptype)
        ptype = ptype[0].decode()

        # if information updates are needed
        if ptype == 'H':
            # refresh the matching hello timer
            hello = struct.unpack("!cIH", packet)
            
            originIP = hello[1]
            originIP = socket.ntohl(originIP)
            originIP = int.to_bytes(originIP, length=4, byteorder=sys.byteorder)
            originIP = socket.inet_ntoa(originIP) # string

            originPort = socket.ntohs(hello[2])

            neighbor = (originIP, originPort)

            # responds to a node coming back online if needed 
            if neighbor in neighbors: 
                neighbors[neighbor] = datetime.now()
            else:
                neighbors[neighbor] = datetime.now()
                nodeSeqNum[neighbor] = -1
                topology[neighbor] = []
                topology[SELF].append(neighbor)
                buildForwardTable()
                infodump()

                # send out a lsm reflecting the update
                mySeqNum = mySeqNum + 1

                for n in neighbors:
                    myIP = socket.inet_aton(HOST)
                    myIP = int.from_bytes(myIP, sys.byteorder)
                    myIP = socket.htonl(myIP)

                    myPort = socket.htons(args.port)

                    # Pack each tuple into a binary string using struct.pack
                    packed_neighbors = b""
                    for pair in topology[SELF]:
                        packed_tup = struct.pack("!15sH", pair[0].encode(), socket.htons(pair[1]))
                        packed_neighbors += packed_tup
                        
                    lsmHeader = struct.pack("!cHIIH", 'L'.encode(), socket.htons(ogNodeCount-1),
                                            socket.htonl(mySeqNum), myIP, myPort)
                    
                    lsmPacket = lsmHeader + packed_neighbors

                    sock.sendto(lsmPacket, n)
                    last_lsm = datetime.now()

        elif ptype == 'L':
            # update topology if needed
            header = packet[:13]
            lsm = struct.unpack("!cHIIH", header)

            seqnum = socket.ntohl(lsm[2]) # 4-byte is just way easier 

            originIP = lsm[3]
            originIP = socket.ntohl(originIP)
            originIP = int.to_bytes(originIP, length=4, byteorder=sys.byteorder)
            originIP = socket.inet_ntoa(originIP) # string

            originPort = socket.ntohs(lsm[4])

            node = (originIP, originPort)

           
            if node in nodeSeqNum and node != SELF:
                 # only update if sequence number is greater than previous value
                if nodeSeqNum[node] < seqnum:
                    nodeSeqNum[node] = seqnum
                    # Unpack the binary string into a list of tuples
                    packed_neighbors = packet[13:]
                    node_neighbors = []
                    while packed_neighbors:
                        # packed_tup = packed_neighbors[:17] + packed_neighbors[15:17].ljust(4, b"\x00")
                        packed_tup = packed_neighbors[:17]
                        pair = struct.unpack("!15sH", packed_tup)
                        # node_neighbors.append((pair[0].decode().strip("\x00"), pair[1]))
                        node_neighbors.append( (pair[0].decode().strip("\x00"), socket.ntohs(pair[1]) ) )
                        packed_neighbors = packed_neighbors[17:]

                    # update topology and forwarding tables only if needed
                    if node in topology and topology[node] != node_neighbors:
                        # notice if anything is dropped, and then remove it from the topology 
                        for n in topology[node]:
                            if n not in node_neighbors and n != SELF:
                                print('tried to drop: '+str(n))                           
                                for j in topology:
                                    if n in topology[j]:
                                        topology[j].remove(n)
                                if n in topology:
                                    topology.pop(n)

                        topology[node] = node_neighbors 
                        infodump()              
                        buildForwardTable()
                        infodump()
                        
            else: # this means a node has come back online after being off
                pass 


        forwardpacket(packet)

    except socket.error:       
        pass

    # check to see if neighbors are expired

    remove = []
    for n in neighbors:
        if (datetime.now()-neighbors[n]).total_seconds() > 2*hello_rate:
            remove.append(n)
           
    while remove:
        # print("Things to remove: "+str(remove))     
        n = remove.pop()
        # print('------------------------REMOVING :'+str(n))
        neighbors.pop(n)
        nodeSeqNum.pop(n)
        #  topology[SELF].remove(n)
        for e in topology:
            if n in topology[e]:
                topology[e].remove(n)
        
        if n in topology:
            topology.pop(n)

        buildForwardTable()

        infodump()

        # send out a lsm reflecting the update
        mySeqNum = mySeqNum + 1

        for n in neighbors: # TODO rewrite this so that you can remove and refactor during the loop
            myIP = socket.inet_aton(HOST)
            myIP = int.from_bytes(myIP, sys.byteorder)
            myIP = socket.htonl(myIP)

            myPort = socket.htons(args.port)

            # Pack each tuple into a binary string using struct.pack
            packed_neighbors = b""
            for pair in topology[SELF]:
                packed_tup = struct.pack("!15sH", pair[0].encode(), socket.htons(pair[1]))
                packed_neighbors += packed_tup
                
            lsmHeader = struct.pack("!cHIIH", 'L'.encode(), socket.htons(ogNodeCount-1),
                                    socket.htonl(mySeqNum), myIP, myPort)
            
            lsmPacket = lsmHeader + packed_neighbors

            sock.sendto(lsmPacket, n)
            last_lsm = datetime.now()
            

    # check if it is time to send hellos and links

    # the hellos
    if (datetime.now()-last_hello).total_seconds() > hello_rate:
        for n in neighbors:
            myIP = socket.inet_aton(HOST)
            myIP = int.from_bytes(myIP, sys.byteorder)
            myIP = socket.htonl(myIP)

            myPort = socket.htons(args.port)

            helloHeader = struct.pack("!cIH", 'H'.encode(), myIP, myPort)

            sock.sendto(helloHeader, n)
        last_hello = datetime.now()

    # the lsm's
    if (datetime.now() - last_lsm).total_seconds() > lsm_rate:
        mySeqNum = mySeqNum + 1

        for n in neighbors:
            myIP = socket.inet_aton(HOST)
            myIP = int.from_bytes(myIP, sys.byteorder)
            myIP = socket.htonl(myIP)

            myPort = socket.htons(args.port)

            # Pack each tuple into a binary string using struct.pack
            packed_neighbors = b""
            for pair in topology[SELF]:
                packed_tup = struct.pack("!15sH", pair[0].encode(), socket.htons(pair[1]))
                packed_neighbors += packed_tup
                
            lsmHeader = struct.pack("!cHIIH", 'L'.encode(), socket.htons(len(topology)),
                                    socket.htonl(mySeqNum), myIP, myPort)
            
            lsmPacket = lsmHeader + packed_neighbors

            sock.sendto(lsmPacket, n)

        last_lsm = datetime.now()

            
# This method decides if the packet needs to be forwarded, and if so does it
def forwardpacket(packet):
    global forwardingTable
    ptype = packet[:1]
    ptype = struct.unpack("!c",ptype)
    ptype = ptype[0].decode()

    # if it is a link state packet
    if ptype == 'L':
        lmsHead = struct.unpack("!cHIIH", packet[:13])
        ttl = socket.ntohs(lmsHead[1])
        # if ttl is positive, it gets forwarded, otherwise it dies
        if ttl > 0:
            ttl -= 1
            ttl = socket.htons(ttl)
            lmsHead = struct.pack("!cHIIH", lmsHead[0], ttl, lmsHead[2], lmsHead[3], lmsHead[4])
            payload = packet[13:]
            packet = lmsHead + payload

            for n in neighbors:       
                sock.sendto(packet, n)
    elif ptype =='T': # if it is a routetrace packet
        rtHead = struct.unpack("!cHIHIH", packet[:15])

        destIP = rtHead[4]
        destIP = socket.ntohl(destIP)
        destIP = int.to_bytes(destIP, length=4, byteorder=sys.byteorder)
        destIP = socket.inet_ntoa(destIP) # string

        destPort = socket.ntohs(rtHead[5])

        dest = (destIP, destPort)

        ttl = socket.ntohs(rtHead[1])

        
        if dest == SELF or ttl <= 0: # final route trace hop, success or fail 
            packed_tup = struct.pack("!15sH", HOST.encode(), socket.htons(args.port))
            packet += packed_tup
            # payload = packet[15:]

            # packet = rtHead + payload

            rtIP = rtHead[2]
            rtIP = socket.ntohl(rtIP)
            rtIP = int.to_bytes(rtIP, length=4, byteorder=sys.byteorder)
            rtIP = socket.inet_ntoa(rtIP) # string

            rtPort = socket.ntohs(rtHead[3])

            rt = (rtIP, rtPort)
           
            sock.sendto(packet, rt)
        
        elif dest not in forwardingTable:
            packed_tup = struct.pack("!15sH", 'err'.encode(), socket.htons(0))
            packet += packed_tup
            # payload = packet[15:]

            # packet = rtHead + payload

            rtIP = rtHead[2]
            rtIP = socket.ntohl(rtIP)
            rtIP = int.to_bytes(rtIP, length=4, byteorder=sys.byteorder)
            rtIP = socket.inet_ntoa(rtIP) # string

            rtPort = socket.ntohs(rtHead[3])

            rt = (rtIP, rtPort)
           
            sock.sendto(packet, rt)
        else:
            ttl -= 1
            ttl = socket.htons(ttl)
            # print(str(rtHead))
            rtHead = struct.pack("!cHIHIH", rtHead[0], ttl, rtHead[2], rtHead[3], rtHead[4], rtHead[5])
            
            packed_tup = struct.pack("!15sH", HOST.encode(), socket.htons(args.port))
            packet += packed_tup
            payload = packet[15:]

            packet = rtHead + payload

            sock.sendto(packet, forwardingTable[dest])


    elif ptype =='R' or ptype == 'D' or ptype == 'E': # if it is a data packet
        # figure this out once the rest is working
        ipheader = packet[9:33]
        ipheader = struct.unpack("!IHIHIHIH", ipheader)

        lastIP = ipheader[0]
        lastIP = socket.ntohl(lastIP)
        lastIP = int.to_bytes(lastIP, length=4, byteorder=sys.byteorder)
        lastIP = socket.inet_ntoa(lastIP) # string

        lastPort = socket.ntohs(ipheader[1])

        last = (lastIP, lastPort)

        if SELF == last:
            destIP = ipheader[2]
            destIP = socket.ntohl(destIP)
            destIP = int.to_bytes(destIP, length=4, byteorder=sys.byteorder)
            destIP = socket.inet_ntoa(destIP) # string

            destPort = socket.ntohs(ipheader[3])

            dest = (destIP, destPort)
            sock.sendto(packet, dest)
        elif last not in forwardingTable:
            destIP = ipheader[4]
            destIP = socket.ntohl(destIP)
            destIP = int.to_bytes(destIP, length=4, byteorder=sys.byteorder)
            destIP = socket.inet_ntoa(destIP) # string

            destPort = socket.ntohs(ipheader[5])

            dest = (destIP, destPort)
            # create a new end packet s = 0 len = 1 to notify failure
            endhead = struct.pack("!cII", 'E'.encode(), socket.htonl(0), socket.htonl(1))
            
            ipheader = struct.pack("!IHIHIHIH", ipheader[4], ipheader[5], ipheader[6], ipheader[7],
                                   ipheader[0],ipheader[1],ipheader[2],ipheader[3])
            head = endhead + ipheader
            
            sock.sendto(head,dest)
        else:
            sock.sendto(packet, forwardingTable[last])



# builds and returns a forwarding table that is based on 
# the topology map that is passed into it. This assumes that
# the given topology map is correct.
def buildForwardTable():
    # find the entry for this emulator
    global forwardingTable
    global SELF
    global topology
    forwardingTable.clear()

    confirmed = {SELF}
    tentative = [(SELF, None)]

    while tentative:
        curNode, prevNode = tentative.pop(0)
        
        if curNode != SELF:
            if prevNode != SELF:
                forwardingTable[curNode] = prevNode
            else:
                forwardingTable[curNode] = curNode

        if curNode in topology:
            for neighbor in topology[curNode]:
                if neighbor not in confirmed:
                    confirmed.add(neighbor)
                    tentative.append((neighbor, curNode))
        else:
            topology[curNode] = []

def infodump():
    print('Topology: ')
    for node in topology:
        # print(str(node)+': '+str(topology[node]))
        s = str(node[0])+','+str(node[1])
        for i in topology[node]:
            s += ' '+str(i[0])+','+str(i[1])
        print(s)

    print('\nForwarding Table: ')
    for node in forwardingTable:
        # print(str(node)+': '+str(forwardingTable[node]))
        s = str(node[0])+','+str(node[1])
        
        s += str(' '+forwardingTable[node][0])+','+str(forwardingTable[node][1])
        print(s)
    # print('\nNeighbors: ')
    # for node in neighbors:
    #     print(str(node)+': '+str(neighbors[node]))
    print('\n')

    

# read topology
readtopology()
# for node in topology:
#     print(str(node)+': '+str(topology[node]))

# build initial forwarding Table
buildForwardTable()
# for node in forwardingTable:
#     print(str(node)+': '+str(forwardingTable[node]))

# build initial timing table for neighbors
initTime = datetime.now()
for neighbor in topology[SELF]:
    neighbors[neighbor] = initTime
# for neighbor in neighbors:
#     print(str(neighbor)+': '+str(neighbors[neighbor]))

# build initial sequence number table for lsm packets
for node in topology:
    nodeSeqNum[node] =  mySeqNum

infodump()
while(True):
    createroutes()
             