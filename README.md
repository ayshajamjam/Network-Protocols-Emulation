# Network Protocols Emulation

## Go-Back-N

## Instructions to Run

**Node**: python3 gbnnode.py <self-port> <peer-port> <window-size> [ -d <value-of-n> | -p <value-of-p>]

- python3 gbnnode.py 1111 2222 5 -d 4
- python3 gbnnode.py 2222 1111 5 -d 2

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