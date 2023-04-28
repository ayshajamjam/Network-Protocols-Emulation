import socket
from socket import *
import threading
import sys
import json
from checks import *
from node_new import *

if __name__ == "__main__":
    
    if(len(sys.argv) != 6):
        print("Incorrect number of arguments")
        sys.exit(0)
    
    self_port = int(sys.argv[1])
    peer_port = int(sys.argv[2])
    window_size = int(sys.argv[3])
    drop_method = sys.argv[4]
    drop_value = 0
    
    if(drop_method == '-d'):
        try:
            drop_value = int(sys.argv[5])
        except:
            print("Error: -d should have integer value provided")
            sys.exit(0)
    else:
        try:
            drop_value = float(sys.argv[5])
        except:
            print("Error: -p should have float value provided between 0 and 1")
            sys.exit(0)

    if(checkPort(self_port) and checkPort(peer_port) and checkDropMethod(drop_method, drop_value)):
        node = Node(self_port, peer_port, window_size, drop_method, drop_value)
        node.nodeSend()