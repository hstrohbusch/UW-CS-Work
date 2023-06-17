# This is the emulator, which acts betwen the sender and the requester
# it emulates what a netork is like
# implements logging, queueing, sending, and logging

# Useful python documents to read are argparse, socket.bind, socket.sendto, 
# socket.recvfrom, socket.gethostbyname
import argparse
from datetime import datetime
import random
import socket
import struct
import sys
import random

parser = argparse.ArgumentParser()

parser.add_argument('-p', "--port",required=True , type=int)        # port of sender
parser.add_argument('-q', "--queue_size",required=True, type=int)   # size of all 3 queues
parser.add_argument('-f', "--filename",required=True)               # name of forwarding table file
parser.add_argument('-l', "--log",required=True)                    # name of the logging file

args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)
hostname = socket.gethostname()
# print(hostname)
HOST = socket.gethostbyname(hostname)

try:
    sock.bind((HOST, args.port))
except Exception as e: 
    print(e)
    exit(1)

# import socket
# temp = socket.gethostname()
# print(temp)
# temp = socket.gethostbyname(temp)
# print(temp)
# temp2 = socket.inet_aton(temp)
# print(temp2)
# temp3 = socket.inet_ntoa(temp2)
# print(temp3)
# print(socket.gethostbyaddr(temp3))

# open tracker and extract the relevant lines
forwardingTable = []

with open(args.filename, 'r') as reader:
    line = reader.readlines()
    for l in line:
        entries = l.split()
        # we are only going to look at entries that are available to this emulator
        # we can get away with looking at this once because its static
        if entries[0] == hostname and int(entries[1]) == args.port:
            #print([entries[2],entries[3],entries[4],entries[5],entries[6],entries[7]] )
            forwardingTable.append((entries[2],entries[3],
                                    entries[4],entries[5],entries[6],entries[7]))
            # print(entries)

#print(forwardingTable) 
#print(forwardingTable[1][1])           

# set up logging 
f = open(args.log, "w")
f.close()

# set up queueing
lowest = []
middle = []
highest = []

# set up delaying
delayStart = datetime.now()
delayed = False 
delta = -1
hold = [None, [None, None, None, None, None, None, None, None ]]

while(1):
    # receive a packet non-blockingly
    try:
        packet, paddr = sock.recvfrom(5146) # max request size
        # print('caught')
        # execution only goes to here if a packet is received
        ipheader = packet[:17]
        ipheader = struct.unpack("!cIHIHI", ipheader)
        #print(ipheader)

        priority = ipheader[0].decode()
        src_ip = ipheader[1]
        src_ip = socket.ntohl(src_ip)
        src_ip = int.to_bytes(src_ip, length=4, byteorder=sys.byteorder)
        src_ip = socket.inet_ntoa(src_ip)
        src_name = socket.gethostbyaddr(src_ip)[0]
        src_port = socket.ntohs(ipheader[2])
        dest_ip = ipheader[3]
        dest_ip = socket.ntohl(dest_ip)
        dest_ip = int.to_bytes(dest_ip, length=4, byteorder=sys.byteorder)
        dest_ip = socket.inet_ntoa(dest_ip)

        dest_name = socket.gethostbyaddr(dest_ip)[0]
        dest_port = socket.ntohs(ipheader[4])
        # length = socket.ntohl(ipheader[5])

        header = packet[17:26]
        header = struct.unpack("!cII", header)
        ptype = header[0].decode()
        length = socket.ntohl(header[2])

        # look through entries for a match
        found = False
        # print('dest: '+str(dest_ip)+ ' '+str(dest_name)+' '+str(dest_port))
        # print('src: '+str(src_ip)+ ' '+str(src_name)+' '+str(src_port))
        for entry in forwardingTable:
            # print(entry)
            if entry[0] == dest_name and int(entry[1]) == dest_port:
                found = True

                if priority == '1':
                    if len(highest) >= args.queue_size and (ptype == 'A' or ptype == 'D'):
                        # print('no room in highest queue, log it drop it')
                        f = open(args.log, "a")
                        f.write("-----\n")
                        f.write("Reason:      priority queue 1 was full \n")
                        f.write("Source:      "+ src_name +", "+str(src_port)+"\n")
                        f.write("Destination: "+ dest_name +", "+str(dest_port)+"\n")
                        f.write("Time:        "+str(datetime.now())+"\n")
                        f.write("Priority:    "+ priority +"\n")
                        f.write("Size:        "+ str(length)+ "\n")
                        f.write("-----\n")
                        f.close()
                        break
                    else:
                        highest.append([packet, entry, ptype])
                        break
                elif priority == '2':
                    if len(middle) >= args.queue_size and (ptype == 'A' or ptype == 'D'):
                        # print('no room in middle queue, log it drop it')
                        f = open(args.log, "a")
                        f.write("-----\n")
                        f.write("Reason:      Priority queue 2 was full\n")
                        f.write("Source:      "+ src_name +", "+str(src_port)+"\n")
                        f.write("Destination: "+ dest_name +", "+str(dest_port)+"\n")
                        f.write("Time:        "+str(datetime.now())+"\n")
                        f.write("Priority:    "+ priority +"\n")
                        f.write("Size:        "+ str(length)+ "\n")
                        f.write("-----\n")
                        f.close()
                        break
                    else:
                        middle.append([packet, entry, ptype])
                        break
                elif priority == '3':
                    if len(lowest) >= args.queue_size and (ptype == 'A' or ptype == 'D'):
                        # print('add to lowest queue, log it drop it')
                        f = open(args.log, "a")
                        f.write("-----\n")
                        f.write("Reason:      No forwarding entry found\n")
                        f.write("Source:      "+ src_name +", "+str(src_port)+"\n")
                        f.write("Destination: "+ dest_name +", "+str(dest_port)+"\n")
                        f.write("Time:        "+str(datetime.now())+"\n")
                        f.write("Priority:    "+ priority +"\n")
                        f.write("Size:        "+ str(length)+ "\n")
                        f.write("-----\n")
                        f.close()
                        break
                    else:
                        lowest.append([packet, entry, ptype])
                        break
                else:
                    #print('incorrect priority formatting or queue is full')
                    f = open(args.log, "a")
                    f.write("-----\n")
                    f.write("Reason:      Incorrect formatting of packet\n")
                    f.write("Source:      "+ src_name +", "+str(src_port)+"\n")
                    f.write("Destination: "+ dest_name +", "+str(dest_port)+"\n")
                    f.write("Time:        "+str(datetime.now())+"\n")
                    f.write("Priority:    "+ priority +"\n")
                    f.write("Size:        "+ str(length)+ "\n")
                    f.write("-----\n")
                    f.close()

                break

        if(found == False):
            # print('droped a packet, no such destination, should be logged somewhere')
            f = open(args.log, "a")
            f.write("-----\n")
            f.write("Reason:      No matching entry found\n")
            f.write("Source:      "+ src_name +", "+str(src_port)+"\n")
            f.write("Destination: "+ dest_name +", "+str(dest_port)+"\n")
            f.write("Time:        "+str(datetime.now())+"\n")
            f.write("Priority:    "+ priority +"\n")
            f.write("Size:        "+ str(length)+ "\n")
            f.write("-----\n")
            f.close()

    except socket.error:
        
        now = datetime.now()

        # if none delayed, remove from queue and start delay if possible
        if not delayed:
            if len(highest) > 0:
                hold = highest.pop(0)
                delta = int(hold[1][4])
                delayStart = now
                delayed = True
            elif len(middle) > 0:
                hold = middle.pop(0)
                delta = int(hold[1][4])
                delayStart = now
                delayed = True
            elif len(lowest) > 0:
                hold = lowest.pop(0)
                delta = int(hold[1][4])
                delayStart = now
                delayed = True
        
        # if currently delayed and not expired back loop
        # when the delay expires either send on or drop
        if (now-delayStart).total_seconds()*1000 >= delta and delayed:
            delayed = False
            # figure out whether to drop or send the packet
            # never dropping r or e packets
            if random.random()*100 < int(hold[1][5]) and (hold[2] == 'A' or hold[2] == 'D'):
                # print('dropped a packet, log it')
                f = open(args.log, "a")
                f.write("-----\n")
                f.write("Reason:      loss event occurred\n")
                f.write("Source:      "+ src_name +", "+str(src_port)+"\n")
                f.write("Destination: "+ dest_name +", "+str(dest_port)+"\n")
                f.write("Time:        "+str(datetime.now())+"\n")
                f.write("Priority:    "+ priority +"\n")
                f.write("Size:        "+ str(length)+ "\n")
                f.write("-----\n")
                f.close()
                hold = [None, [None, None, None, None, None, None, None, None ]]
            else:
                nextHost = socket.gethostbyname(hold[1][2]), int(hold[1][3])
                sock.sendto(hold[0], nextHost)
                # print('forwarded')
                hold = [None, [None, None, None, None, None, None, None, None ]]
             