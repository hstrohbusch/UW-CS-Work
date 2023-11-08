#include <stdio.h>
#include "udp.h"

#include "message.h"
#include "mfs.h"
#include <time.h>
#include <stdlib.h>

// client code
int main(int argc, char *argv[]) {
    struct sockaddr_in addrSnd, addrRcv;

    int MIN_PORT = 20000;
    int MAX_PORT = 40000;

    srand(time(0));
    int port_num = (rand() % (MAX_PORT - MIN_PORT) + MIN_PORT);

    // Bind random client port number
    int sd = UDP_Open(port_num);
    int rc = UDP_FillSockAddr(&addrSnd, "localhost", 20724);

    MFS_Creat();
    MFS_Lookup();

/*    message_t m;

    m.mtype = MFS_READ;
    printf("client:: send message %d\n", m.mtype);
    rc = UDP_Write(sd, &addrSnd, (char *) &m, sizeof(message_t));
    if (rc < 0) {
	printf("client:: failed to send\n");
	exit(1);
    }

    printf("client:: wait for reply...\n");
    rc = UDP_Read(sd, &addrRcv, (char *) &m, sizeof(message_t));
    printf("client:: got reply [size:%d rc:%d type:%d]\n", rc, m.rc, m.mtype);*/
    return 0;
}

