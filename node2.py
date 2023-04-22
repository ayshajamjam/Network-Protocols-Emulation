import socket
from socket import *
import threading
import sys
import json
import time
import ipaddress
from random import *

IP = '127.0.0.1'
lock = threading.Lock()

class DvNode:
    def __init__(self, local_port, neighbor_ports, last):
        self.local_port = local_port
        self.neighbor_ports = neighbor_ports
        self.last = last

    def info(self):
        print("Local port: ", self.local_port)
        print("Neighbor ports: ", self.neighbor_ports)
        print("Last: ", self.last)