import socket
from socket import *
import threading
import sys
import json
from checks import *
from node2 import *

if __name__ == "__main__":
    
    if(len(sys.argv) < 4):
        print("Incorrect number of arguments. Need at least 4.")
        sys.exit(0)
    elif(len(sys.argv) % 2 == 1 and sys.argv[len(sys.argv) - 1] != 'last'):
        print("Incorrect number of arguments")
        sys.exit(0)

    # Get local port
    local_port = int(sys.argv[1])
    if(not checkPort(local_port)):
        print("Check local port")
        sys.exit(0)
    
    # Get last variable
    last = 0
    if(sys.argv[len(sys.argv) - 1] == 'last'):
        last = 1

    # Get neighbor-port:loss-rate
    dv = {}
    neighbor_ports = set()
    for arg in range(2, len(sys.argv) - 1, 2):
        if(not checkPort(int(sys.argv[arg]))):
            print("Check neighbor ports")
            sys.exit(0)
        elif(not checkLossRate(float(sys.argv[arg+1]))):
            print("Check loss rates")
            sys.exit(0)
        else:
            dv[int(sys.argv[arg])] = float(sys.argv[arg+1])
            neighbor_ports.add(int(sys.argv[arg]))

    node = DvNode(local_port, neighbor_ports, dv, last)
    print('\n')
    node.info()
    node.print_routing_table()
    print('\n')

    # Start first round of sending dv to neighbors
    node.nodeSend()