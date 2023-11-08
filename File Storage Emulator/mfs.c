#include <stdio.h>
#include "mfs.h"
#include "message.h"
#include "udp.h"
#include <time.h>
#include <stdlib.h>
#include <sys/select.h>

struct sockaddr_in addrSnd, addrRcv;
int sd;
int rc;

//  Takes a host name and port number and uses those 
//  to find the server exporting the file system.
int MFS_Init(char *hostname, int port) {
  int MIN_PORT = 20000;
  int MAX_PORT = 40000;

  srand(time(0));
  int port_num = (rand() % (MAX_PORT - MIN_PORT) + MIN_PORT);

  // Bind random client port number
  sd = UDP_Open(port_num);
  if (sd < 0) {
	//printf("MFS_Init failed: UDP_Open failed somehow\n");
	return -1;
    }
    
  rc = UDP_FillSockAddr(&addrSnd, hostname, port);
  if (rc < 0) {
	//printf("MFS_Init failed: UDP_FillSockAddr failed somehow\n");
	return -1;
    }
    
  return 0;
}

int MFS_Lookup(int pinum, char *name) {
  message_t m;
  m.mtype = MFS_LOOKUP;
  m.inum = pinum;
  //strcpy(m.name , name);
  memcpy(m.name, name, 28);
  //printf("---Lookup is looking for pinum: %d  mfsentry with name: %s\n",pinum,name);
      
  UDP_Write(sd, &addrSnd, (char *) &m, sizeof(message_t));
  //printf("client:: request lookup\n");
  UDP_Read(sd, &addrRcv, (char *) &m, sizeof(message_t));
  //printf("client:: received response lookup name %s\n", m.name);//rc=%d, inum=%d\n, msg=%s", m.rc, m.inum, m.name);
  
  if(m.rc == 0) { // success
      return m.inum;
  } else {
      //printf("Error message from lookup: %s\n",m.name);
      //printf("directs checked = %d\n",m.nbytes);
      perror(m.name);
      return -1;
  }
}

int MFS_Stat(int inum, MFS_Stat_t *m) {
    message_t mes;
    mes.mtype = MFS_STAT;
    mes.inum = inum;
    
    UDP_Write(sd, &addrSnd, (char *) &mes, sizeof(message_t));
    //printf("client:: request stat\n");
    UDP_Read(sd, &addrRcv, (char *) &mes, sizeof(message_t));
    //printf("client:: received response stat\n");
    
    if(mes.rc == 0) { // success 
    	//m->type = mes.type;
    	//m->size = mes.nbytes;
    	memcpy(&m->type, &mes.type, 4);
    	memcpy(&m->size, &mes.nbytes, 4);
      return 0;
      
    }
    perror(mes.name);
    return -1;
}

int MFS_Write(int inum, char *buffer, int offset, int nbytes) {
    message_t m;
    m.inum = inum;
    m.offset = offset;
    m.nbytes = nbytes;
    //strcpy(m.buffer, buffer);
    memcpy(m.buffer,buffer,MFS_BLOCK_SIZE);
    m.mtype = MFS_WRITE;
    
    UDP_Write(sd, &addrSnd, (char *) &m, sizeof(message_t));
    printf("client:: request write with inum: %d offset: %d\n", inum, offset);
    
    struct timeval timeout;
    timeout.tv_sec = 5;
    timeout.tv_usec = 0;

    fd_set readfds;
    FD_ZERO(&readfds);
    FD_SET(sd, &readfds);
    
    int wait = select(sd+1, &readfds, NULL, NULL, &timeout);
    
    if(wait == -1) { 
      perror("select failed");
      return -1;
    } else if(wait == 0) { // ran out of time
        UDP_Write(sd, &addrSnd, (char *) &m, sizeof(message_t));
        printf("client:: request write again\n");
    } else { // ready to move on
        UDP_Read(sd, &addrRcv, (char *) &m, sizeof(message_t));
        printf("client:: received response wrote in datablock %d \n",m.type);
        
        if(m.rc == 0)
          return 0;      
        else {
            perror(m.name);
            return -1;
        }
    }
    
    // should not reach here
    return -1;
    
}

int MFS_Read(int inum, char *buffer, int offset, int nbytes) {
    message_t m;
    m.inum = inum;
    m.offset = offset;
    m.nbytes = nbytes;
    m.mtype = MFS_READ;
    
    UDP_Write(sd, &addrSnd, (char *) &m, sizeof(message_t));
    printf("client:: request read with offset %d\n", offset);
    UDP_Read(sd, &addrRcv, (char *) &m, sizeof(message_t));
    
    printf("client:: received response for read from %d through %d and tried to read datablock %d \n", offset, offset + nbytes, m.mtype);
        
    if(m.rc == 0){                 
        //strcpy(buffer, m.buffer);
        memcpy(buffer, m.buffer, MFS_BLOCK_SIZE);
        return 0;
    } 
    
    perror(m.name);
    return -1;
    
}

int MFS_Creat(int pinum, int type, char *name) {
    
    if(strlen(name) > 28) {
      perror("name is too long");
      return -1;
    }
    
    message_t m;
    m.inum = pinum;
    m.type = type;
    strcpy(m.name, name);
    m.mtype = MFS_CRET;
    
    //printf("---MFS_Creat is trying to create with pinum: %d\ttype:%d\tname: %s\n",pinum, type, name);
    
    UDP_Write(sd, &addrSnd, (char *) &m, sizeof(message_t));
    //printf("client:: request create\n");
    
    struct timeval timeout;
    timeout.tv_sec = 5;
    timeout.tv_usec = 0;
    
    fd_set readfds;
    FD_ZERO(&readfds);
    FD_SET(sd, &readfds);
    
    int wait = select(sd+1, &readfds, NULL, NULL, &timeout);
    
    if(wait == -1) { 
      perror("select failed");
      //printf("select failed here in creat\n");
      return -1;
    } else if(wait == 0) { // ran out of time
        UDP_Write(sd, &addrSnd, (char *) &m, sizeof(message_t));
        //printf("client:: request create again\n");
    } else { // ready to move on
        UDP_Read(sd, &addrRcv, (char *) &m, sizeof(message_t));
        printf("client:: received response create\n");
        //printf("client received a response in creat\n");
        //printf("response for creat. rc=%d\n", m.rc);
        if(m.rc == 0){
          //printf("creat in parentinode %d direct entry %d made a mfsentry with name %s and inum %d\n",pinum, m.type,m.name,m.nbytes);
          return 0;      
        }else {
            //printf("client failed in creat\n");
            perror(m.name);
            return -1;
        }
    }
    
    // should not reach here
    //printf("entered an unexpected area\n");
    return -1;
    
}

int MFS_Unlink(int pinum, char *name) {
    message_t m;
    m.inum = pinum;
    strcpy(m.name, name);
    m.mtype = MFS_UNLINK;
    
    UDP_Write(sd, &addrSnd, (char *) &m, sizeof(message_t));
    //printf("client:: request unlink\n");
    
    struct timeval timeout;
    timeout.tv_sec = 5;
    timeout.tv_usec = 0;
    
    fd_set readfds;
    FD_ZERO(&readfds);
    FD_SET(sd, &readfds);
    
    int wait = select(sd+1, &readfds, NULL, NULL, &timeout);
    
    if(wait == -1) { 
      perror("select failed");
      return -1;
    } else if(wait == 0) { // ran out of time
        UDP_Write(sd, &addrSnd, (char *) &m, sizeof(message_t));
        //printf("client:: request unlink again\n");
    } else { // ready to move on
        UDP_Read(sd, &addrRcv, (char *) &m, sizeof(message_t));
        //printf("client:: received response unlink\n");
        
        if(m.rc == 0)
          return 0;      
        else {
            //printf("unlinks fail was %s\n",m.name);
            perror(m.name);
            return -1;
        }
    }
    
    // should not reach here
    return -1;
}

int MFS_Shutdown() {
    printf("MFS Shutdown\n");
    message_t m;
    m.mtype = MFS_SHUTDOWN;
    UDP_Write(sd, &addrSnd, (char *) &m, sizeof(message_t));
    UDP_Close(sd);
    return 0;
}
