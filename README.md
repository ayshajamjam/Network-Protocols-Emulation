# Network Protocols Emulation

## Part 1) Go-Back-N

## Instructions to Run

**Node**: python3 gbnnode.py <self-port> <peer-port> <window-size> [ -d <value-of-n> | -p <value-of-p>]

- python3 gbnnode.py 1111 2222 5 -d 0
- python3 gbnnode.py 2222 1111 5 -d 0

## Checks

### Incorrect Number of Arguments
- python3 gbnnode.py

### Incorrect Port Number
- python3 gbnnode.py 1111111 2222 5 -d 4
- python3 gbnnode.py 1111 22222222 5 -d 4
- python3 gbnnode.py 11 2222 5 -d 4
- python3 gbnnode.py 1111 22 5 -d 4
- python3 gbnnode.py 11111111 221111122 5 -d 4

### Incorrect Drop Method
- python3 gbnnode.py 1111 2222 5 -k 4

### Incorrect Drop Value
- python3 gbnnode.py 1111 2222 5 -d 0.24
- python3 gbnnode.py 1111 2222 5 -p 4
- python3 gbnnode.py 1111 2222 5 -p 0
- python3 gbnnode.py 1111 2222 5 -p 1
- python3 gbnnode.py 1111 2222 5 -p -1
- python3 gbnnode.py 1111 2222 5 -p 3.5

## Part 2) Distance Vector

### Instructions to run

**$** python3 dvnode.py <local-port> <neighbor1-port> <loss-rate-1> <neighbor2-port> <loss-rate-2> ... [last]

- python3 dvnode.py 1111 2222 .1 3333 .5
- python3 dvnode.py 2222 1111 .1 3333 .2 4444 .8
- python3 dvnode.py 3333 1111 .5 2222 .2 4444 .5
- python3 dvnode.py 4444 2222 .8 3333 .5 last


### Incorrect num arguments
python3 dvnode.py 1111
python3 dvnode.py 1111 2222
python3 dvnode.py 1111 2222 .1 3333

### Incorrect local port
python3 dvnode.py 1000 2222 .1
python3 dvnode.py 1111111 2222 .1

### Incorrect neighbor port
python3 dvnode.py 1111 222 .1
python3 dvnode.py 1111 222222222 .1

### Incorrect loss rate
python3 dvnode.py 1111 2222 -1
python3 dvnode.py 1111 2222 10

# Everything correct (not including last)
python3 dvnode.py 1111 2222 .1
python3 dvnode.py 1111 2222 .1 3333 .5

# Everything correct (including last)
python3 dvnode.py 1111 2222 .1 last
python3 dvnode.py 1111 2222 .1 3333 .5 last

- **dvnode** Program name.
- **local-port** The UDP listening port number (1024-65534) of the node.
- **neighbor#-port** The UDP listening port number (1024-65534) of one of the neighboring nodes.
- **loss-rate-#** This will be used as the link distance to the <neighbor#-port>. It is between 0-1 and represents the probability of a packet being dropped on that link. For this section of the assignment you do not have to implement dropping of packets. Keep listing the pair of <neighbor-port> and <loss-rate> for all your neighboring nodes.
- **last** Indication of the last node information of the network. The program should understand this arg as optional (hence represented in brackets above). Upon the input of the command with this argument, the routing message exchanges among the nodes should kick in.
- **ctrl+C (exit)** Use ctrl+C to exit the program.