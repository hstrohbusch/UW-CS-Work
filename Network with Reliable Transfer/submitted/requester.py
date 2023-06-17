# This is the receiver, which uses looks up file name (args.file) in the
# table in tracker, and sends requests to the appopriate senders to send their
# entire portion of the file. The order to be requested and sent is shown in tracker 

# Tracker layout
# Filename, ID, Sender_hostname, Sender_port

# Useful python documents to read are argparse, socket.bind, socket.sendto, 
# socket.recvfrom, socket.gethostbyname
import argparse
from datetime import datetime
import socket
import struct
import sys

parser = argparse.ArgumentParser()

parser.add_argument('-p', "--port",required=True , type=int)    # port of sender
parser.add_argument('-o', "--file",required=True, )               # file requested
parser.add_argument('-f', "--f_hostname", required=True)
parser.add_argument('-e', "--f_port", required=True, type=int)
parser.add_argument('-w', "--window", required=True, type=int)

args = parser.parse_args()

# print('port: ', args.port, ' requester port: ', args.requester_port)

if(args.port <= 2049 or args.port >= 65536):
    print('invalid port number')
    exit(0)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
reqHOST = socket.gethostbyname(socket.gethostname())

HOST = (socket.gethostbyname(args.f_hostname), args.f_port)

# print(socket.gethostname())
try:
    sock.bind((reqHOST, args.port))
except Exception as e: 
    print(e)
    exit(1)

# TODO: read in from tracker file names and id's
#       THEN sort them by id
#       THEN request 

# open tracker and extract the relevant lines
requests = []

with open('tracker.txt', 'r') as reader:
    line = reader.readlines()
    for l in line:
        entries = l.split()
        if entries[0] == args.file:
            requests.append( tuple([entries[1],entries[2],entries[3]]) )

f = open(args.file,'wb')
f.close()

if len(requests) == 0:
    print("No such file with that name in tracker")
    exit(0)

requests.sort()

for i in range(len(requests)):
    # print(requests[i])
    # create and send the request
    destAddr = socket.gethostbyname(requests[i][1])
    destPort = int(requests[i][2])

    header = struct.pack("!cII", 'R'.encode(), socket.htonl(0), socket.htonl(args.window))

    reqAddrInt = socket.htonl(int.from_bytes(socket.inet_aton(reqHOST), sys.byteorder))   
    destAddrInt = socket.htonl(int.from_bytes(socket.inet_aton(destAddr), sys.byteorder))

    # print('original: '+reqHOST)
    # print('bytes: '+str(socket.inet_aton(reqHOST)))
    # print('host int:'+str(int.from_bytes(socket.inet_aton(reqHOST), sys.byteorder)))
    # print('inside: '+str(reqAddrInt))
    # print('translated: '+str(socket.ntohl(reqAddrInt)))
    # print(destAddrInt)

    ipReqHeader = struct.pack("!cIHIHI", '1'.encode(), reqAddrInt , socket.htons(args.port), 
                               destAddrInt, socket.htons(destPort), socket.htonl(264) )
    # print(ipReqHeader)
    header_and_payload =  ipReqHeader + header + args.file.encode()

    # import struct
    # temp = struct.pack("!cIH", '1'.encode(), 3232235664, 5000 )
    # temp2 = struct.unpack("!cIH", temp)
    # print(temp2)

    sock.sendto(header_and_payload, HOST)
    end = False
    init_time = datetime.now()
    dpackets = 0
    dbytes = 0

    writebuf = [None] * args.window
    curwindow = 0


    while(end == False):
    
        sfullpacket, saddr = sock.recvfrom(5146) # max request size
        time = datetime.now()
        rtime = time.isoformat(sep=' ', timespec='milliseconds')

        sheader = sfullpacket[17:26]
        spayload = sfullpacket[26:]
        sheader = struct.unpack("!cII", sheader)  

        ptype = sheader[0].decode()
        seqnum = socket.ntohl(sheader[1])-1
        # print(seqnum)

        # detect if we are in a new window
        # this is necessary to see if the sender has given up on
        # sending a packet and moved on
        # as a bonus, this also shows when a full window has arrived

        if(seqnum//args.window > curwindow):
            curwindow = seqnum//args.window

            # write everything we have 
            for pay in writebuf:
                if pay != None:
                    with open(args.file, 'ab') as f:
                        f.write(pay)
            
            writebuf.clear()
            writebuf = [None] * args.window
        

        if(ptype == 'D'):
            # send back an ack 
            header = struct.pack("!cII", 'A'.encode(), socket.htonl(seqnum+1), socket.htonl(0))

            ipReqHeader = struct.pack("!cIHIHI", '1'.encode(), reqAddrInt, socket.htons(args.port), 
                               destAddrInt, socket.htons(destPort), socket.htonl(26) )
            
            ack = ipReqHeader + header
            sock.sendto(ack, HOST)
            # print('sent ack for s '+str(seqnum))
            
            # if it is a new packet...
            if(writebuf[seqnum%args.window] == None):
                if dbytes == 0:
                    init_time = time            

                dpackets += 1
                dbytes += socket.ntohl(sheader[2])
                writebuf[seqnum%args.window]= spayload

            
            # # suppressed indiviual data packet info dumps

            # # print('DATA Packet')
            # # print('recv time:\t', rtime)
            # # print('sender addr:\t', str(saddr[0])+':'+str(saddr[1]))
            # # print('sequence:\t',socket.ntohl(sheader[1]))
            # # print('length:\t\t', socket.ntohl(sheader[2]))
            # # print('payload:\t', spayload[:4].decode(),'\n')
        elif(ptype == 'E'):
            end = True

            # write everything we have 
            for pay in writebuf:
                if pay != None:
                    with open(args.file, 'ab') as f:
                        f.write(pay)
            
            writebuf.clear()

            print('END Packet')
            print('recv time:\t', rtime)
            print('sender addr:\t', str(saddr[0])+':'+str(saddr[1]))
            print('sequence:\t',socket.ntohl(sheader[1]))
            print('length:\t\t', socket.ntohl(sheader[2]))
            print('payload:\t', spayload[:4].decode(),'\n')

            print('Summary')
            print('sender addr:\t\t', str(saddr[0])+':'+str(saddr[1]))
            print('Total Data packets:\t', dpackets)
            print('Total Data bytes:\t', dbytes)
            print('Average packets/second:\t', round(dpackets / (time-init_time).total_seconds()))
            print('Duration of the test:\t',round( (time-init_time).total_seconds()*1000 ),'ms\n')


sock.close()
