Distributed Systems: Introduction
A simple UDP client and server:

client.c: example client code, sends a message to the server and waits for a reply
server.c: example server code, waits for messages indefinitely and replies
Both use udp.c as a simple UDP communication library.

The Makefile builds client and server executables. Type make to do this.

To run: type server & to run the server in the background; then type client to run the client. You will likely then want to kill the server if you are done.

If you want to run these on different machines, you'll have to change the client to send messages to the machine the server is running upon, instead of localhost.

.........

This project was built from the assigned libraries that were assigned to us. Our main work was to put everything together to emulate file storage and accessing. We were also given a testing script, the results of which are in the file "runtests.log". I received full points for this project. I have included the summary of runtests.log below

Summary:
test build PASSED
 (build project using make)

test shutdown PASSED
 (init server and client then call shutdown)

test creat PASSED
 (creat a file and check with lookup)

test write PASSED
 (write then read one block)

test stat PASSED
 (stat a regular file)

test overwrite PASSED
 (overwrite a block)

test maxfile PASSED
 (write largest possible file)

test maxfile2 PASSED
 (write more blocks than possible)

test dir1 PASSED
 (check root for dot entries)

test dir2 PASSED
 (create a new directory and check it)

test baddir PASSED
 (try to create a file with a file parent inode)

test baddir2 PASSED
 (try to lookup a file with a file parent inode)

test unlink PASSED
 (unlink a file)

test unlink2 PASSED
 (unlink a directory)

test empty PASSED
 (unlink a non-empty directory)

test name PASSED
 (name too long)

test persist PASSED
 (restart server after creating a file)

test bigdir PASSED
 (create a directory with 126 files)

test deep PASSED
 (create many deeply nested directories)

Passed 19 of 19 tests.
Overall 19 of 19
