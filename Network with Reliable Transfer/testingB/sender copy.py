# This is the sender, which chunks a requested file and sends
# each file chunk via UDP packets to the requester

# Useful python documents to read are argparse, socket.bind, socket.sendto, 
# socket.recvfrom, socket.gethostbyname
import argparse
from datetime import datetime
import socket
import struct
import os
import time
import sys

parser = argparse.ArgumentParser()

parser.add_argument('-p', "--port",required=True , type=int)            # port of sender
parser.add_argument('-g', "--requester_port",required=True, type=int)   # port of receiver
parser.add_argument('-r', "--rate",required=True,type=int)              # packets sent/second
parser.add_argument('-q', "--seq_no",required=True,type=int)            # start seq number
parser.add_argument('-l', "--length",required=True,type=int)            # payload length bytes
parser.add_argument('-f', "--f_hostname", required=True)
parser.add_argument('-e', "--f_port", required=True,type=int)
parser.add_argument('-i', "--priority", required=True)
parser.add_argument('-t', "--timeout", required=True,type=int)

args = parser.parse_args()

# print('port: ', args.port, ' requester port: ', args.requester_port)

if(args.port <= 2049 or args.port >= 65536):
    print('invalid port number')
    exit(0)

if(args.requester_port <= 2049 or args.requester_port >= 65536):
    print('invalid requester port number')
    exit(0)

if args.rate<= 0 or args.length <=0:
    print('invalid arguments')
    exit(0)

 
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sendHOST = socket.gethostbyname(socket.gethostname())
# print(sendHOST)

HOST = (socket.gethostbyname(args.f_hostname), args.f_port)

try:
    sock.bind((sendHOST, args.port))
except Exception as e: 
    print(e)
    exit(1)

# receive the request
fullpacket, addr = sock.recvfrom(281) # max request size

# separate payload and header
ipheader = fullpacket[:17]
header = fullpacket[17:26]
payload = fullpacket[26:]

ipheader = struct.unpack("!cIHIHI", ipheader)
header = struct.unpack("!cII", header)

#decode
ptype = header[0].decode()
seqnum = socket.ntohl(header[1])
window = socket.ntohl(header[2])

payload = payload.decode()

if(ptype != 'R' or seqnum != 0 ):
    print('incorrect request header formatting')
    exit(0)

sendAddrInt = socket.htonl(int.from_bytes(socket.inet_aton(sendHOST), sys.byteorder))   
# print(ptype)
# print(seqnum)
# print(length)
# print(payload)

s = 1

# check to make sure it exists
if os.path.exists(payload) == False:
    # send the end packet
    endheader = struct.pack("!cII", 'E'.encode(), socket.htonl(s), socket.htonl(0))
    
    ipendheader = struct.pack("!cIHIHI", args.priority.encode(), sendAddrInt, 
                              socket.htons(args.port), ipheader[1], ipheader[2], socket.htonl(9) )
    
    combineHead = ipendheader + endheader
    sock.sendto(combineHead, HOST)

    print("END Packet")
    print('send time:\t', datetime.now().isoformat(sep=' ', timespec='milliseconds'))
    print('requester addr:\t', str(addr[0])+':'+str(addr[1]))
    print('sequence:\t',s)
    print('length:\t\t 0')
    print('payload:\t \n')

    exit(0)

# figure out how many packets we need to send
l = args.length
fsize = os.path.getsize(payload)
num_data_packets = fsize // l

# if fsize % l != 0:
#     num_data_packets += 1

# print(payload, ' is ', fsize, ' bytes long')
# print('since the payload length is ', int(args.length), ' bytes, we need ', num_data_packets, ' sends')

# we want non-blocking reception of ack packets at this point
# sock.setblocking(False)

with open(payload, 'rb') as reader:
    # send the data
    w = 0
    winbuf = []
    for j in range(num_data_packets):
        
        data = reader.read(l)
        dataheader = struct.pack("!cII", 'D'.encode(), socket.htonl(s), socket.htonl(l))
        ipDataHeader = struct.pack("!cIHIHI", args.priority.encode(), sendAddrInt, 
                            socket.htons(args.port), ipheader[1], ipheader[2], socket.htonl(9+l) )

        header_and_payload = ipDataHeader + dataheader + data
        sendtime = datetime.now()
        winbuf.append((s, header_and_payload, sendtime, 0)) # seq, stuff, last send time, attempts 
        w = w + 1
        s = s + 1
        sock.sendto(header_and_payload, HOST)

        # print("DATA Packet")
        # print('send time:\t', datetime.now().isoformat(sep=' ', timespec='milliseconds'))
        # print('requester addr:\t', str(addr[0])+':'+str(addr[1]))
        # print('sequence:\t',s)
        # print('length:\t\t', l)
        # print('payload:\t', data[:4].decode(),'\n')
        
        time.sleep(1/args.rate)           
            
        if w >= window: # A window has been sent, check to make sure it was received
            # wait for acks, resend packets if needed
            while len(winbuf) != 0:
                # look for ack packets
                acks = sock.recv(window*26) # max size is if all acks are here already
                print('received some number of acks')
                sli = 0
                

                while len(acks) != sli:
                    # a single packet
                    curpack = acks[sli:(sli + 26)]
                    # check to make sure its an ack packet
                    head = curpack[17:26]
                    head = struct.unpack("!cII", head)

                    if(head[0].decode()!='A'):
                        print('received something that is not an ack')
                        exit(1)

                    # look at its sequence num and remove matching
                    pacnum = socket.ntohl(head[1])
                    print('ack received: '+head[0].decode()+' '+ str(pacnum)+' '+str(socket.ntohl(head[2]) ) )
                    # for i in range(len(winbuf)):
                    #     if winbuf[i][0] == pacnum:
                    #         winbuf.remove(i)
                    #         break
                    print('sender window: '+str((s-2)//window)+'\tack window: '+str((pacnum-1)//window))

                    if (s-2)//window == (pacnum-1)//window:
                        print('same window '+str((s-2)//window))
                        # pacnum = pacnum % window
                        match = False
                        i = 0

                        while not match and i < len(winbuf):
                            if winbuf[i][0] == pacnum:
                                print('removed entry '+str(pacnum)+' from winbuf')
                                winbuf.pop(i)
                                match = True
                            i = i + 1
                    
                    sli = sli + 26

                # check buffer for expired timeouts

                i = 0

                while i < len(winbuf):
                    if( (datetime.now()-winbuf[i][2]).total_seconds()*1000 >= args.timeout ):
                        if(winbuf[i][3] < 5):
                            # attempt to resend
                            print('resending '+str(winbuf[i][0]))
                            sock.sendto(winbuf[i][1], HOST)
                            #pkt[3] = pkt[3] + 1
                            winbuf[i] = (winbuf[i][0], winbuf[i][1], winbuf[i][2], winbuf[i][3]+1)
                            # time.sleep(1/args.rate) 
                            time.sleep(0.25)
                        else:
                            # no more resend attempts left
                            print('failed to resend '+ str(winbuf[i][0]))
                            winbuf.pop(i)
                            i-=1
                    i = i + 1


            w = 0
    
    if fsize % l != 0:

        data = reader.read(fsize % l)
        dataheader = struct.pack("!cII", 'D'.encode(), socket.htonl(s), socket.htonl(fsize % l))
        ipDataHeader = struct.pack("!cIHIHI", args.priority.encode(), sendAddrInt, 
                socket.htons(args.port), ipheader[1], ipheader[2], socket.htonl(9+(fsize % l)) )

        header_and_payload = ipDataHeader + dataheader + data
        # add to buffer
        sendtime = datetime.now()
        winbuf.append((s, header_and_payload, sendtime, 0)) # seq, stuff, last send time, attempts 
        s = s + 1
        w = w + 1
        # send it out
        sock.sendto(header_and_payload, HOST)

        # print("DATA Packet")
        # print('send time:\t', datetime.now().isoformat(sep=' ', timespec='milliseconds'))
        # print('requester addr:\t', str(addr[0])+':'+str(addr[1]))
        # print('sequence:\t',s)
        # print('length:\t\t', fsize % l)
        # print('payload:\t', data[:4].decode(),'\n')
        
        time.sleep(1/args.rate)
            

# wait for last of the acks if any, resend if needed
if w >= window: # A window has been sent, check to make sure it was received
    # wait for acks, resend packets if needed
    while len(winbuf) != 0:
        # look for ack packets
        acks = sock.recv(window*26) # max size is if all acks are here already
        print('received some number of acks')
        sli = 0
        

        while len(acks) != sli:
            # a single packet
            curpack = acks[sli:(sli + 26)]
            # check to make sure its an ack packet
            head = curpack[17:26]
            head = struct.unpack("!cII", head)

            if(head[0].decode()!='A'):
                print('received something that is not an ack')
                exit(1)

            # look at its sequence num and remove matching
            pacnum = socket.ntohl(head[1])
            print('ack received: '+head[0].decode()+' '+ str(pacnum)+' '+str(socket.ntohl(head[2]) ) )
            # for i in range(len(winbuf)):
            #     if winbuf[i][0] == pacnum:
            #         winbuf.remove(i)
            #         break
            print('sender window: '+str((s-2)//window)+'\tack window: '+str((pacnum-1)//window))

            if (s-2)//window == (pacnum-1)//window:
                print('same window '+str((s-2)//window))
                # pacnum = pacnum % window
                match = False
                i = 0

                while not match and i < len(winbuf):
                    if winbuf[i][0] == pacnum:
                        print('removed entry '+str(pacnum)+' from winbuf')
                        winbuf.pop(i)
                        match = True
                    i = i + 1
            
            sli = sli + 26

        # check buffer for expired timeouts

        i = 0

        while i < len(winbuf):
            if( (datetime.now()-winbuf[i][2]).total_seconds()*1000 >= args.timeout ):
                if(winbuf[i][3] < 5):
                    # attempt to resend
                    print('resending '+str(winbuf[i][0]))
                    sock.sendto(winbuf[i][1], HOST)
                    #pkt[3] = pkt[3] + 1
                    winbuf[i] = (winbuf[i][0], winbuf[i][1], winbuf[i][2], winbuf[i][3]+1)
                    # time.sleep(1/args.rate) 
                    time.sleep(0.25)
                else:
                    # no more resend attempts left
                    print('failed to resend '+ str(winbuf[i][0]))
                    winbuf.pop(i)
                    i-=1
            i = i + 1

    w = 0
        
# send the end packet

endheader = struct.pack("!cII", 'E'.encode(), socket.htonl(s), socket.htonl(0))
ipEndHeader = struct.pack("!cIHIHI", args.priority.encode(), sendAddrInt, 
                socket.htons(args.port), ipheader[1], ipheader[2], socket.htonl(9) )

endhead = ipEndHeader + endheader
sock.sendto(endhead, HOST)

print("END Packet")
print('send time:\t', datetime.now().isoformat(sep=' ', timespec='milliseconds'))
print('requester addr:\t', str(addr[0])+':'+str(addr[1]))
print('sequence:\t',s)
print('length:\t\t 0')
print('payload:\t \n')


sock.close()
