import socket
from socket import *
import threading
import sys
import json
import time
import ipaddress
from random import *
import ast

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

    def nodeListen(self):
        # Need to declare a new socket bc socket is already being used to send
        node_listen_socket = socket(AF_INET, SOCK_DGRAM)
        node_listen_socket.bind(('', self.local_port))
        
        while True:
            buffer, sender_address = node_listen_socket.recvfrom(4096)
            buffer = buffer.decode()

            print(("[{}] Message received at Node {} from Node {}").format(time.time(), self.local_port, sender_address[1]))
            dv_res = ast.literal_eval(buffer)
            print(dv_res)
            print(type((ast.literal_eval(buffer))))

    def nodeSend(self):
        # Create UDP socket
        node_send_socket = socket(AF_INET, SOCK_DGRAM)

        # Multithreading
        listen = threading.Thread(target=self.nodeListen)
        listen.start()

    def send_dv(self):
        # Create UDP socket
        node_send_socket = socket(AF_INET, SOCK_DGRAM)

        # Multithreading
        listen = threading.Thread(target=self.nodeListen)
        listen.start()

        for neighbor in self.neighbor_ports:
            print(("[{}] Message sent from Node {} to Node {}").format(time.time(), self.local_port, neighbor))
            node_send_socket.sendto(str(self.neighbor_ports).encode(), (IP, neighbor))