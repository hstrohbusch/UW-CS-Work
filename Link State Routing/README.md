The purpose of this assignment was to emulate how different nodes in a network connect to each other and react accordingly, theoretically allowing communcation across all nodes

Here is an example running of the program

NOTE: this program is designed to work with an initial topography state that looks like the one below, where the format is ip addr, port, showing how the nodes are initially connected

![topography](https://github.com/hstrohbusch/UW-CS-Work/assets/71783165/5b3b9808-e5eb-415f-b212-c852e850b716)


Each emulator.py represents a node, and is launched by identifying that nodes port and the file containing the topography

![init](https://github.com/hstrohbusch/UW-CS-Work/assets/71783165/6d7534fa-a78a-43b5-b6d7-aa3a1479d344)


The emulators then read in the data from the topography file...

![init read](https://github.com/hstrohbusch/UW-CS-Work/assets/71783165/d4db8bbd-8370-4d54-b293-7dcc1f3d254d)


... And stabilize appropriately if not all emulators are launched

![init stable](https://github.com/hstrohbusch/UW-CS-Work/assets/71783165/88d189c4-6ad0-416d-ad25-d35bec26b6fd)



Moving on, I manually kill the emulator started at port 5000 (left). The rest of the emulators detect this and update appropriately via linked state routing

![5000 killed](https://github.com/hstrohbusch/UW-CS-Work/assets/71783165/1047a13b-7af9-43c1-9449-f5f4d9bd0baa)


Then, I re-initialize 5000. The rest of the emulators detect this and rebuild their topographies and forwarding tables appropriately

![5000 reboot](https://github.com/hstrohbusch/UW-CS-Work/assets/71783165/115e4a85-df74-4137-b16e-91a28490728a)
