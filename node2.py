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
    def __init__(self, local_port, dv, last):
        self.local_port = local_port
        self.dv = dv
        self.last = last
        self.routing_table = {} # key: neighbor port, value: tuple: (min_distance, next_hop_node)

        # Construct routing table
        for node in self.dv:
            self.routing_table[node] = (self.dv[node], None)

        # Keep track of number of times this node has forwarded its dv
        self.forward_count = 0

    def info(self):
        print("Local port: ", self.local_port)
        print("Distance vector: ", self.dv)
        print("Last: ", self.last)

    def print_routing_table(self):
        print(("[{}] Node {} Routing Table").format(time.time(), self.local_port))
        for node in self.routing_table:
            next_hop = self.routing_table[node][1]
            distance = self.routing_table[node][0]
            if(next_hop == None):
                print(("- ({}) --> Node {}").format(distance, node))
            else:
                print(("- ({}) --> Node {}; Next hop --> Node {}").format(distance, node, next_hop))


    def nodeListen(self):
        # Need to declare a new socket bc socket is already being used to send
        node_listen_socket = socket(AF_INET, SOCK_DGRAM)
        node_listen_socket.bind(('', self.local_port))
        
        while True:
            buffer, sender_address = node_listen_socket.recvfrom(4096)
            buffer = buffer.decode()

            print(("[{}] Message received at Node {} from Node {}").format(time.time(), self.local_port, sender_address[1]))
            dv_res = ast.literal_eval(buffer)   # converts strin containing dv vector to dict
            print(dv_res)

            # Populate routing table
            for node in dv_res:
                if(node != self.local_port and node in self.routing_table.keys()):
                    current_dist = self.dv[node]
                    candidate_dist = dv_res[node]
                    print(node, " >> Node is already in table. ", "current: ", current_dist, ' vs ', "candidate; ", candidate_dist )
                    if(candidate_dist < current_dist):
                        self.dv[node] = candidate_dist
                        self.routing_table[node] = (candidate_dist, sender_address[1])
                elif(node != self.local_port and node not in self.routing_table.keys()):
                    print(node, " >> Need to add new reachable node: ", node)
                    self.dv[node] = dv_res[node]
                    self.routing_table[node] = (dv_res[node], sender_address[1])
                else:
                    print(node, " >> This is the local port.")
            self.print_routing_table()

            # Forward distance vector to neighbors
            self.forward_count += 1

            for neighbor in self.dv:
                print(("[{}] Message sent from Node {} to Node {}").format(time.time(), self.local_port, neighbor))
                node_listen_socket.sendto(str(self.dv).encode(), (IP, neighbor))

    def nodeSend(self):
        # Create UDP socket
        node_send_socket = socket(AF_INET, SOCK_DGRAM)

        # Multithreading
        listen = threading.Thread(target=self.nodeListen)
        listen.start()

    def send_initial_dv(self):
        # Create UDP socket
        node_send_socket = socket(AF_INET, SOCK_DGRAM)
        node_send_socket.bind((IP, self.local_port))

        # Multithreading
        listen = threading.Thread(target=self.nodeListen)
        listen.start()

        self.forward_count += 1
        for neighbor in self.dv:
            print(("[{}] Message sent from Node {} to Node {}").format(time.time(), self.local_port, neighbor))
            node_send_socket.sendto(str(self.dv).encode(), (IP, neighbor))