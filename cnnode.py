import socket
from socket import *
import threading
import sys
import json
from checks import *
from node3 import *
from node2 import *
from node import *


if __name__ == "__main__":
    
    # Get local port
    local_port = int(sys.argv[1])
    if(not checkPort(local_port)):
        print("Check local port")
        sys.exit(0)
    
    # Get last variable
    last = 0
    if(sys.argv[len(sys.argv) - 1] == 'last'):
        last = 1

    # Assign sender/receiver neighbors
    neighbor_ports = set()
    dv = {}
    receive_probes = {}
    send_probes = {}

    i = 3
    while(sys.argv[i] != 'send'):
        receive_probes[int(sys.argv[i])] = float(sys.argv[i+1])
        dv[int(sys.argv[i])] = float(sys.argv[i+1])
        neighbor_ports.add(int(sys.argv[i]))
        i += 2
    i += 1
    while(i < len(sys.argv) and sys.argv[len(sys.argv) - 1] != 'last'):
        send_probes[int(sys.argv[i])] = 0
        dv[int(sys.argv[i])] = 0
        neighbor_ports.add(int(sys.argv[i]))
        i += 1

    node = CnnNode(local_port, neighbor_ports, dv, last, receive_probes, send_probes)

    print('\n')
    node.info()
    node.print_routing_table()
    print('\n')

    # Start first round of sending dv to neighbors
    node.nodeSend()