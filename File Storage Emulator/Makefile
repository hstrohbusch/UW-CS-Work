make: 
	gcc -Wall -Werror -c server.c
	gcc server.o -o server udp.c
	gcc -c udp.c -o udp.o
	gcc -fPIC -g -c -Wall mfs.c
	gcc -shared -Wl,-soname,libmfs.so -o libmfs.so mfs.o udp.o -lc
	export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:.
	 


SRCS   := server.c mfs.c

OBJS   := ${SRCS:c=o}
PROGS  := ${SRCS:.c=}

clean:
	rm -f server.o
	rm -f udp.o
	rm -f mfs.o
	rm -f client.o
	rm -f client
	rm -f server
	
	
