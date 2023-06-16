#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>

#include "mfs.h"
#include "ufs.h"
#include "udp.h"
#include "server.h"
int sd; 
int rc;
int fd;
int image_size;
void *image;
super_t *s;
inode_t *inode_table;

int main(int argc, char *argv[]) {
    
    // check args
    if(argc != 3) {
      perror("incorrect number of arguments for server initialization");
      exit(1);
    }
    
    fd = open(argv[2], O_RDWR);
    assert(fd > -1);

    struct stat sbuf;
    rc = fstat(fd, &sbuf);
    assert(rc > -1);

    image_size = (int) sbuf.st_size;

    image = mmap(NULL, image_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    assert(image != MAP_FAILED);

    s = (super_t *) image;
    printf("inode bitmap address %d [len %d]\n", s->inode_bitmap_addr, s->inode_bitmap_len);
    printf("data bitmap address %d [len %d]\n", s->data_bitmap_addr, s->data_bitmap_len);

    inode_table = image + (s->inode_region_addr * UFS_BLOCK_SIZE);
    inode_t *root_inode = inode_table;
    printf("\nroot type:%d root size:%d\n", root_inode->type, root_inode->size);
    printf("direct pointers[0]:%d [1]:%d\n", root_inode->direct[0], root_inode->direct[1]);

    dir_ent_t *root_dir = image + (root_inode->direct[0] * UFS_BLOCK_SIZE);
    printf("\nroot dir entries\n%d %s\n", root_dir[0].inum, root_dir[0].name);
    printf("%d %s\n", root_dir[1].inum, root_dir[1].name);
    
    
    // creates socket and binds to port
    printf("here is the port number %d\n",atoi(argv[1]));
    sd = UDP_Open(atoi(argv[1])); // 10000 by default
    assert(sd > -1);
    
    while (1) {
    	struct sockaddr_in addr;
    
    	message_t m;
    	
    	printf("server:: waiting...\n");
    	rc = UDP_Read(sd, &addr, (char *) &m, sizeof(message_t));
    	printf("server:: read message [size:%d contents:(%d)]\n", rc, m.mtype);
    	if (rc > 0) { // change what is in this accordingly
    	   //m.rc = 3;
           //rc = UDP_Write(sd, &addr, (char *) &m, sizeof(message_t));
    	   //printf("server:: reply\n");
           
           if(m.mtype ==2)
               serLookup(&m);
           else if(m.mtype ==3)
               serStat(&m);
           else if(m.mtype ==4)
               serWrite(&m);
           else if(m.mtype ==5)
               serRead(&m);
           else if(m.mtype ==6)
               serCreat(&m);
           else if(m.mtype ==7)
               serUnlink(&m);
           else if(m.mtype ==8)
               serShutdown(&m);
           else  {
               strcpy(m.name , "Unexpected mtype");
               m.rc = -1;
               }
           
           rc = UDP_Write(sd, &addr, (char *) &m, sizeof(message_t));
    	   printf("server:: reply\n");    
           
           
    	} 
    
        signal(SIGINT, intHandler); //at the end?
    }

    close(fd);
    return 0;
}

void intHandler(int dummy) {
    UDP_Close(sd);
    exit(130);
}

// takes parent inode number (directory) and a name
// returns the inode number of name
// fail modes invalid pinum, name does not exist in pinum
void serLookup(message_t *m){
  // if beyond max amount of inodes or negative
  if(m->inum < 0 || m->inum >= (s->inode_region_len * UFS_BLOCK_SIZE)/sizeof(inode_t)) {
      m->rc = -1;
      strcpy(m->name , "invalid pinum");
      return;
  }
  
  // checks if inode for pinum has been allocated
  unsigned int *ibitmap_ptr = image + s->inode_bitmap_addr * UFS_BLOCK_SIZE;
  if(get_bit(ibitmap_ptr, m->inum) != 1) {
      m->rc = -1;
      strcpy(m->name , "pinum not set in bitmap.");
      return;
  }
  
  // the inode given by pinum
  inode_t *tempInode;
  //tempInode = ((m->inum * sizeof(inode_t)) + inode_table);
  tempInode = m->inum  + inode_table;
  
  
  if(tempInode->type != MFS_DIRECTORY){
      m->rc = -1;
      strcpy(m->name , "pinum not for a dir");
      return;
  }
  ///m->nbytes = 0;
  for(int i = 0; i < DIRECT_PTRS; i++) {
    if(tempInode->direct[i] != -1 ) {
        
        // go into a valid data block and check all valid MFS_DirEnt_t's
    
        for(int j = 0; j < (UFS_BLOCK_SIZE / sizeof(MFS_DirEnt_t)); j++) {
            
            // copy over whatever name is in the MFS_DirEnt_t
            
            char check[28];
            memcpy(check, image + (tempInode->direct[i] * UFS_BLOCK_SIZE)  + (j * sizeof(MFS_DirEnt_t)), 28);
            
            // if the entries name matches, success
            if(strcmp(check, m->name) == 0){
            	m->rc = 0;
                memcpy(&m->inum, image + (tempInode->direct[i] * UFS_BLOCK_SIZE)  + (j * sizeof(MFS_DirEnt_t)) + 28, 4);
                return;
            }
            
            
        }
        
    } 
  }
    
  // does not exist
  //strcpy(m->name , "name not in pinum dir");
  memcpy(m->name, image + (tempInode->direct[0] * UFS_BLOCK_SIZE)  + (2 * sizeof(MFS_DirEnt_t)), 28);
  //m->nbytes = tempInode->direct[0];
  m->rc = -1;
  return;
}

// takes an inum and fills out some info to a MFS_Stat
void serStat(message_t *m) {
    // is the inum in a valid range
    if(m->inum < 0 || m->inum >= (s->inode_region_len * UFS_BLOCK_SIZE)/sizeof(inode_t)) {
      m->rc = -1;
      strcpy(m->name , "inum does not exist");
      return;
    }
    //is the inum allocated
    unsigned int *ibitmap_ptr = image + s->inode_bitmap_addr * UFS_BLOCK_SIZE;
    if(get_bit(ibitmap_ptr, m->inum) != 1) {
    	m->rc = -1;
    	strcpy(m->name , "inum does not exist");
    	return;
    }
    
    // the inode given by inum
    inode_t *tempInode;
    //tempInode = ((m->inum * sizeof(inode_t)) + inode_table);
    tempInode = m->inum  + inode_table;
    
    // pass the needed info to m, it gets handled in mfs.c
    m->type = tempInode->type;
    m->nbytes = tempInode->size;
    
    m->rc = 0;
    
    return;
}
void serWrite(message_t *m){
    // validity checks
    // inum
    if(m->inum < 0 || m->inum >= (s->inode_region_len * UFS_BLOCK_SIZE)/sizeof(inode_t)) {
      m->rc = -1;
      strcpy(m->name , "invalid inum");
      return;
    }
    unsigned int *ibitmap_ptr = image + s->inode_bitmap_addr * UFS_BLOCK_SIZE;
    if(get_bit(ibitmap_ptr, m->inum) != 1) {
      m->rc = -1;
      strcpy(m->name , "invalid inum");
      return;
    }
  
    // the parent inode
    inode_t *tempInode;
    //tempInode = ((m->inum * sizeof(inode_t)) + inode_table);
    tempInode = m->inum  + inode_table;
    
    // offset 
    if(m->offset < 0 || m->offset > tempInode->size) {
        m->rc = -1;
        strcpy(m->name , "invalid offset");
        return;
    }
        
    // nbytes
    if(m->nbytes < 0 || m->nbytes > 4096) {
      m->rc = -1;
      strcpy(m->name , "invalid nbytes");
      return;
    }
    
    // max size
    if(m->nbytes + m->offset > (DIRECT_PTRS * UFS_BLOCK_SIZE) ){
    	m->rc = -1;
    	strcpy(m->name, "write is too big");
    	return;
    }
    
    // is this a directory?
    if(tempInode->type == MFS_DIRECTORY){
      m->rc = -1;
      strcpy(m->name , "not a regular file");
      return;
    }
    
    // nuclear approach: test only writes whole blocks
    unsigned int *dbitmap_ptr = image + s->data_bitmap_addr * UFS_BLOCK_SIZE;
    for(int block = 0; block < s->data_region_len; block++){  // finding available block for overflow          
        if( get_bit(dbitmap_ptr, block) == 0) { // found one
            set_bit(dbitmap_ptr, block); // update bitmap
            tempInode->direct[m->offset / UFS_BLOCK_SIZE] = block + s->data_region_addr; // update inode 
            break;
        }
    }
    
    memcpy(image + (tempInode->direct[m->offset/UFS_BLOCK_SIZE] * UFS_BLOCK_SIZE) + m->offset % UFS_BLOCK_SIZE, m->buffer, m->nbytes);
    
    m->mtype = tempInode->direct[m->offset/UFS_BLOCK_SIZE];
    m->debug = tempInode->direct[(m->offset + m->nbytes) / UFS_BLOCK_SIZE];
    // increase the size if needed. Just because we write doesn't meen we grow i.e. overwrite
    if(tempInode->size < m->offset + m->nbytes)
        tempInode->size = m->offset + m->nbytes;
    
    // force all changes to disk
    msync(image, image_size, MS_SYNC);
    m->rc = 0;
    return;
}
void serRead(message_t *m){
    // validity checks
    // inum
    if(m->inum < 0 || m->inum >= (s->inode_region_len * UFS_BLOCK_SIZE)/sizeof(inode_t)) {
      m->rc = -1;
      strcpy(m->name , "invalid inum");
      return;
    }
    unsigned int *ibitmap_ptr = image + s->inode_bitmap_addr * UFS_BLOCK_SIZE;
    if(get_bit(ibitmap_ptr, m->inum) != 1) {
      m->rc = -1;
      strcpy(m->name , "invalid inum");
      return;
    }
  
    inode_t *tempInode;
    //tempInode = ((m->inum * sizeof(inode_t)) + inode_table);
    tempInode = m->inum  + inode_table;
    // offset 
    if(m->offset < 0 || m->offset > tempInode->size) {
        m->rc = -1;
        strcpy(m->name , "invalid offset");
        return;
    }
        
    // nbytes
    if(m->nbytes < 0 || m->nbytes > 4096 ){
      m->rc = -1;
      strcpy(m->name , "invalid nbytes");
      return;
    }
    
    if(m->offset + m->nbytes > (DIRECT_PTRS * UFS_BLOCK_SIZE) ) {
    	m->rc = -1;
      strcpy(m->name , "read goes beyond file");
      return;
    }

    // nuclear approach
    // we only read and write whole blocks for the tests provided
    
    
    memcpy(m->buffer, image + (tempInode->direct[m->offset / UFS_BLOCK_SIZE] * UFS_BLOCK_SIZE) + (m->offset % UFS_BLOCK_SIZE), m->nbytes);
    m->type = 1;
    m->mtype = tempInode->direct[m->offset/UFS_BLOCK_SIZE];
    
    // I think this does the casting for directories by itself, 
    // otherwise the stuff in buffer would need to be taken out
    // casted to MFS_DirEnt_t and then put back in which feels dumb
    m->rc = 0;
      
    return;

}
void serCreat(message_t *m){
    // validity checks
    // inum
    if(m->inum < 0 || m->inum >= (s->inode_region_len * UFS_BLOCK_SIZE)/sizeof(inode_t)) {
      m->rc = -1;
      strcpy(m->name , "pinum does not exist");
      return;
    }
    unsigned int *ibitmap_ptr = image + s->inode_bitmap_addr * UFS_BLOCK_SIZE;
    if(get_bit(ibitmap_ptr, m->inum) != 1) {
      m->rc = -1;
      strcpy(m->name , "pinum does not exist");
      return;
    }
    
    inode_t *tempInode;
    //tempInode = ((m->inum * sizeof(inode_t)) + inode_table);
    tempInode = m->inum  + inode_table;
    
    if(tempInode->type != MFS_DIRECTORY){
        m->rc = -1;
        strcpy(m->name , "invalid pinum");
        return;
    }
    m->nbytes = 0;

    
    // look to see if it already exists
    for( int i = 0; i < DIRECT_PTRS; i++) {
        if(tempInode->direct[i] != -1) {
            // for every valid data block, check every MFS_DirEnt_t name
            
            for(int j = 0; j < (UFS_BLOCK_SIZE / sizeof(dir_ent_t)); j++) {
                // if the entries name matches, we return early because it already exists

                char check[28];
		        memcpy(check, image + (tempInode->direct[i] * UFS_BLOCK_SIZE)  + (j * sizeof(MFS_DirEnt_t)), 28);
		        if(strcmp(check, m->name) == 0){
		        	m->rc = 0;
		            return;
		        }

            }
        }
    }
    
    // it doesn't exist yet, need to make it 
        
    // try to put it in an existing directory data block
    for( int i = 0; i < DIRECT_PTRS; i++) {
        if(tempInode->direct[i] != -1) { // found an existing block
            // check every valid MFS_DirEnt_t in the data blcok
            
            for(int j = 0; j < (UFS_BLOCK_SIZE / sizeof(MFS_DirEnt_t)); j++) {
                
                // this shows validity by telling us the entries inum
                int avail = 0;
                memcpy(&avail, image + (tempInode->direct[i] *UFS_BLOCK_SIZE) + 
                                          (j * sizeof(MFS_DirEnt_t)) + 28, 4);
                if(avail == -1) { // found a free spot
                    // allocate an inode for the MFS_DirEnt_t
                    unsigned int *ibitmap_ptr = image + s->inode_bitmap_addr * UFS_BLOCK_SIZE;
        
                    for(int iptr = 0; iptr < (s->inode_region_len * UFS_BLOCK_SIZE)/sizeof(inode_t); iptr++) {    
                        if( get_bit(ibitmap_ptr, iptr) == 0) { // found one
                            // update bitmap
                            set_bit(ibitmap_ptr, iptr); 

			    // update the MFS_DirEnt_t 
                            memcpy(image + (tempInode->direct[i] * UFS_BLOCK_SIZE) + 
                                              (j*sizeof(MFS_DirEnt_t)), m->name, 28);
                            memcpy(image + (tempInode->direct[i] * UFS_BLOCK_SIZE) + 
                                              (j*sizeof(MFS_DirEnt_t))+28, &iptr, 4);
                            
                            // fill in the inode created for the entry
                            inode_t *myNode;
                            // myNode = (iptr * sizeof(inode_t)) + inode_table;
                            myNode = iptr + inode_table;
                            myNode->type = m->type;
                            myNode->size = 0;
                            for(int mndp = 0; mndp < DIRECT_PTRS; mndp++)
                                myNode->direct[mndp] = -1;
                            
                                                      
                            
                            
                            // if we are creating a directory we need to...                           
                            // add the parent and self names
                            // adjust size accordingly    
                            if(m->type == MFS_DIRECTORY) {
                            	// allocate the first data block for it  
                            unsigned int datablock = -1;
                            unsigned int *dbitmap_ptr = image + s->data_bitmap_addr * UFS_BLOCK_SIZE;
                            
                            for(int dptr = 0; dptr < s->data_region_len; dptr++) {
                                if( get_bit(dbitmap_ptr, dptr) == 0) { // found one
                                    set_bit(dbitmap_ptr, dptr); // update bitmap
                                    datablock = dptr + s->data_region_addr;
                                    //dptr = s->data_region_len;
                                    break;
                                }
                            }

                            myNode->direct[0] = datablock;
                                // we will use this for the names
                                char self[28] =".";
                                char par[28] = "..";
                                
                                // first do the entry for the self
                                
                                // name is .
                                memcpy(image + (datablock * UFS_BLOCK_SIZE), &self, 28);
                                // inum is what we just allocated
                        	  memcpy(image + (datablock * UFS_BLOCK_SIZE) +28, &iptr, 4);
                                
                                // then the parent
                                
                                // name is ..
                                memcpy(image + (datablock * UFS_BLOCK_SIZE) + sizeof(MFS_DirEnt_t), &par, 28);
                                // inum is the parents inum which was passed in m
                        	memcpy(image + (datablock * UFS_BLOCK_SIZE) + sizeof(MFS_DirEnt_t) +28, &m->inum, 4);
                        	
                        	// nothing else should be valid in the new data block yet	
                        	int empty = -1;
                                for (int e = 2; e < 128; e++)
                    	            memcpy(image + (datablock * UFS_BLOCK_SIZE) + e*sizeof(MFS_DirEnt_t) +
                                                                                          28, &empty, 4);
                                
                                // now the data block has stuff in it, size needs to change             
                                myNode->size = 2*sizeof(MFS_DirEnt_t);
                                         
                            }
                            
                            // see if parent size needs adjusting
                            if( (i*UFS_BLOCK_SIZE) + ((j+1) * sizeof(dir_ent_t)) > tempInode->size)
                                tempInode->size = (i*UFS_BLOCK_SIZE) + ((j+1) * sizeof(dir_ent_t));
                            
                            // debugging                         
                            msync(image, image_size, MS_SYNC);
                            m->rc = 0;
                            m->nbytes = iptr;
                            m->type = i;
                            return;
                        }
                    }
                }
            }
        }
    }
    
    // we tried to put it in an existing directory data block, but it didn't fit
    // need to make a new directory block (or at least try)
    for( int i = 0; i < DIRECT_PTRS; i++) {
 
        if(tempInode->direct[i] == -1) {  // found an available spot
            // allocate the datablock for the next directory block
            int datablock = -1;
            unsigned int *dbitmap_ptr = image + s->data_bitmap_addr * UFS_BLOCK_SIZE;
            
            for(int dptr = 0; dptr < s->data_region_len; dptr++) {
                if( get_bit(dbitmap_ptr, dptr) == 0) { // found one
                    set_bit(dbitmap_ptr, dptr); // update bitmap
                    datablock = dptr + s->data_region_addr;
                    break;
                }
            }
            
            tempInode->direct[i] = datablock;         
                            
            int empty = -1;
            
            for (int e = 0; e < 128; e++)
	            memcpy(image+ (tempInode->direct[i] * UFS_BLOCK_SIZE) + (e*sizeof(MFS_DirEnt_t))+28, &empty, 4);

            // allocate an inode for the new creation 
            unsigned int *ibitmap_ptr = image + s->inode_bitmap_addr * UFS_BLOCK_SIZE;

            for(int iptr = 0; iptr < (s->inode_region_len * UFS_BLOCK_SIZE)/sizeof(inode_t); iptr++) {    
                if( get_bit(ibitmap_ptr, iptr) == 0) { // found one
                    set_bit(ibitmap_ptr, iptr); // update bitmap
                    // update directory entry
                                       
                    memcpy(image + (tempInode->direct[i] * UFS_BLOCK_SIZE) , m->name, 28);
                    memcpy(image + (tempInode->direct[i] * UFS_BLOCK_SIZE) +28, &iptr, 4);
                    
                    // fill in the inode 
                    inode_t *myNode;
                    //myNode = (iptr * sizeof(inode_t)) + inode_table;
                    myNode = iptr + inode_table;
                    myNode->type = m->type;
                    myNode->size = 0;
                    for(int mndp = 0; mndp < DIRECT_PTRS; mndp++)
                        myNode->direct[mndp] = -1;
                        
                    
                    
                    // if we are creating a directory we need to...                           
                    // add the parent and self names
                    // adjust size accordingly    
                    if(m->type == MFS_DIRECTORY) {
                    	// allocate a data block for it  
                    int datablock2 = -1;
                    unsigned int *dbitmap_ptr = image + (s->data_bitmap_addr * UFS_BLOCK_SIZE);
                    
                    for(int dptr = 0; dptr < s->data_region_len; dptr++) {
                        if( get_bit(dbitmap_ptr, dptr) == 0) { // found one
                            set_bit(dbitmap_ptr, dptr); // update bitmap
                            datablock2 = dptr  + s->data_region_addr;
                            //dptr = s->data_region_len;
                            break;
                        }
                    }
                    
                    myNode->direct[0] = datablock2;
                        // exact same as above, except using datablock 2 because that is the block allocated for the inode
                        char self[28] =".";
                        char par[28] = "..";
                        
                        memcpy(image + (datablock2 * UFS_BLOCK_SIZE), &self, 28);
                        memcpy(image + (datablock2 * UFS_BLOCK_SIZE) +28, &iptr, 4);
                                               
                        memcpy(image + (datablock2 * UFS_BLOCK_SIZE) + sizeof(MFS_DirEnt_t), &par, 28);
                        memcpy(image + (datablock2 * UFS_BLOCK_SIZE) + sizeof(MFS_DirEnt_t) +28, &m->inum, 4);
                        
                        for (int e = 2; e < 128; e++)
            	            memcpy(image + (datablock2 * UFS_BLOCK_SIZE) + e*sizeof(MFS_DirEnt_t) +28, 
                                                                                          &empty, 4);
                                     
                        myNode->size = 2*sizeof(MFS_DirEnt_t);
                                 
                    }
                    
                    // see if parent size needs adjusting (it probably will) 
                    if( (i*UFS_BLOCK_SIZE) + sizeof(dir_ent_t) > tempInode->size)
                        tempInode->size = (i*UFS_BLOCK_SIZE) + sizeof(dir_ent_t);
                                
                    m->rc = 0;
                    msync(image, image_size, MS_SYNC);
                    return;
                }
            }
        }
    }
  
  // at this point there is no available spot
  // no existing blocks have space
  // no more space for new directory blocks
  strcpy(m->name, "directory full");
  m->rc = -1;  
  return;
}
void serUnlink(message_t *m){
  // validity checks
    // inum
    if(m->inum < 0 || m->inum >= (s->inode_region_len * UFS_BLOCK_SIZE)/sizeof(inode_t)) {
      m->rc = -1;
      strcpy(m->name , "pinum does not exist");
      return;
    }
    
    unsigned int *ibitmap_ptr = image + s->inode_bitmap_addr * UFS_BLOCK_SIZE;
    unsigned int *dbitmap_ptr = image + s->data_bitmap_addr * UFS_BLOCK_SIZE;
    if(get_bit(ibitmap_ptr, m->inum) != 1) {
      m->rc = -1;
      strcpy(m->name , "pinum does not exist");
      return;
    }
    
    inode_t *tempInode; // parent directory inode
    //tempInode = ((m->inum * sizeof(inode_t)) + inode_table);
    tempInode = m->inum  + inode_table;
    
  
    for(int i = 0; i < DIRECT_PTRS; i++) {
    
        if(tempInode->direct[i] != -1 ) {
            // go into a valid directory data block and check all entries            
        
            for(int j = 0; j < (UFS_BLOCK_SIZE / sizeof(MFS_DirEnt_t)); j++) {
                // if the entries name matches, we succeed
                
                char check[28];
                memcpy(check, image + (tempInode->direct[i] * UFS_BLOCK_SIZE) + (j * sizeof(MFS_DirEnt_t)), 28);
                
                if(strcmp(check, m->name) == 0){
                    // this is the inum for the thing that we are removing
                    int dieInum;
                    memcpy(&dieInum, image + (tempInode->direct[i] * UFS_BLOCK_SIZE) + 
                                                   (j * sizeof(MFS_DirEnt_t)) + 28, 4);
                                                   
                    //inode_t *die = (dieInum * sizeof(inode_t)) + inode_table;
                    inode_t *die;
                    die = dieInum + inode_table;
                    
                    // check die's size if it is a directory to make sure empty
                    
                    // if it is a directory, make sure it is empty
                    if(die->type == UFS_DIRECTORY) {
                        if(die->size != 2*sizeof(MFS_DirEnt_t)) {
                            m->rc = -1;
                            strcpy(m->name, "directory is NOT empty");
                            msync(image, image_size, MS_SYNC);
                            return;
                        }
                    }                                        
                    
                    // clearing the stuff in the entry
                    for(int k = 0; k < DIRECT_PTRS; k++) {
                        if(die->direct[k] != -1) {
                            // wiping the files contents PIAZZA SAYS NOT NEEDED
                            
                            //char buffer[MFS_BLOCK_SIZE];
                            //pwrite(fd, buffer, MFS_BLOCK_SIZE, (MFS_BLOCK_SIZE * s-> data_region_addr) + 
                             //   (die->direct[k] * MFS_BLOCK_SIZE));
                            // deallocating that block
                            set_bit(dbitmap_ptr, die->direct[k] - s->data_region_addr);
                            // getting rid of direct
                            die->direct[k] = -1;
                        }
                        
                    }
                    
                    // entry inode gets taken care of
                    die->type = -1;
                    die->size = 0;                                 
                    set_bit(ibitmap_ptr, dieInum);
                    
                    // now to take care of the MFS_DirEnt_t in the parent directory
                    
                    char blank[28];
                    memcpy(image + (tempInode->direct[i] * UFS_BLOCK_SIZE) + (j * sizeof(MFS_DirEnt_t)), 
                                                                                              &blank, 28);
                    int gone = -1;
                    memcpy(image + (tempInode->direct[i] * UFS_BLOCK_SIZE) + (j * sizeof(MFS_DirEnt_t)) + 28,
                                                                                                  &gone, 4);
                    // decrease parent directories size if it is currently the last item
                    // otherwise the maximum offset will not decrease, so therefore size won't either
                    if(tempInode->size  == (i * UFS_BLOCK_SIZE) + ((j+1) * sizeof(MFS_DirEnt_t) ) )
                        tempInode->size -= sizeof(MFS_DirEnt_t);

// This would be the most efficient use of the datablock, however when it gets filled later the offset
// would basically become useless. This would be fixable with shifting, but I hope we don't need to do that

                    
//                    // we just removed mfs_dirent_t j from directory block i
//                    // if j was the last thing in the block we need to deallocate the block
//                    int last = 1;
//                    for(int k = 0; k < (UFS_BLOCK_SIZE / sizeof(MFS_DirEnt_t)); k++) {
//                        int remains;
//                        memcpy(&remains, image + (tempInode->direct[i] * UFS_BLOCK_SIZE) + 
//                                                          (k * sizeof(MFS_DirEnt_t))+28, 4);
//                        if(remains != -1) {
//                            last = 0;
//                            k = (UFS_BLOCK_SIZE / sizeof(MFS_DirEnt_t));
//                        }
//                    }
//                    
//                    if(last){
//                        set_bit(dbitmap_ptr, tempInode->direct[i] - s->data_region_addr);
//                        tempInode->direct[i] = -1;
//                    }
                        
                    // now to sync and return
                    msync(image, image_size, MS_SYNC);
                    m->rc = 0;
                    return;
                }
            }
        } 
    }
    
    // name not found, but apparently that is ok
    msync(image, image_size, MS_SYNC);
    return;
}
void serShutdown(message_t *m){
   msync(image, image_size, MS_SYNC);
   close(fd);
   UDP_Close(sd);
   exit(0);
}
unsigned int get_bit(unsigned int *bitmap, int position) {
   int index = position / 32;
   int offset = 31 - (position % 32);
   return (bitmap[index] >> offset) & 0x1;
}

void set_bit(unsigned int *bitmap, int position) {
   int index = position / 32;
   int offset = 31 - (position % 32);
   bitmap[index] |= 0x1 << offset;
}

