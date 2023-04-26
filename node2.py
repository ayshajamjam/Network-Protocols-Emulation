import socket
from socket import *
import threading
import sys
import json
import time
import ipaddress
from random import *
import ast
import copy

IP = '127.0.0.1'
lock = threading.Lock()

class DvNode:
    def __init__(self, local_port, neighbor_ports, dv, last):
        self.local_port = local_port
        self.neighbor_ports = neighbor_ports
        self.dv = dv
        self.last = last
        self.routing_table = {} # key: neighbor port, value: tuple: (min_distance, next_hop_node)

        # Construct routing table
        for node in self.neighbor_ports:
            self.routing_table[node] = (self.dv[node], None)

        # Keep track of number of times this node has forwarded its dv
        self.forward_count = 0

    def info(self):
        print("Local port: ", self.local_port)
        print("Neighbor ports: ", self.neighbor_ports)
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

            old_dv = copy.deepcopy(self.dv)
            print("OLD DV: ", old_dv)

            # Populate routing table
            for node in dv_res:
                if(node != self.local_port and node in self.routing_table.keys()):
                    current_dist = self.dv[node]
                    candidate_dist = round(self.dv[sender_address[1]] + dv_res[node], 1)
                    print(node, " >> Node is already in table. ", "current: ", current_dist, ' vs ', "candidate; ", candidate_dist )
                    if(candidate_dist < current_dist):
                        self.dv[node] = candidate_dist
                        self.routing_table[node] = (candidate_dist, sender_address[1])
                elif(node != self.local_port and node not in self.routing_table.keys()):
                    print("Neighbor ports: ", self.neighbor_ports)
                    print(node, " >> Need to add new reachable node: ", node)
                    self.dv[node] = round(self.dv[sender_address[1]] + dv_res[node], 1)
                    self.routing_table[node] = (round(self.dv[sender_address[1]] + dv_res[node], 1), sender_address[1])
                    print("Neighbor ports: ", self.neighbor_ports)
                else:
                    print(node, " >> This is the local port.")
            
            self.print_routing_table()

            # Forward distance vector to neighbors
            self.forward_count += 1

            print("OLD DV: ", old_dv)
            print("CURRENT DV: ", self.dv)

            # Only forward dv if this node has never forwarded before
            # or if there is a change in the distance vector
            if(self.forward_count == 1):
                print("First time forwarding")
                for neighbor in self.neighbor_ports:
                    print(("[{}] Message sent from Node {} to Node {}").format(time.time(), self.local_port, neighbor))
                    node_listen_socket.sendto(str(self.dv).encode(), (IP, neighbor))
            elif(self.dv != old_dv):
                print("Distance vector has changed")
                for neighbor in self.neighbor_ports:
                    print(("[{}] Message sent from Node {} to Node {}").format(time.time(), self.local_port, neighbor))
                    node_listen_socket.sendto(str(self.dv).encode(), (IP, neighbor))
            else:
                print("Distance vector has not changed")
                print(old_dv)
                print(self.dv)
                sys.exit(0)

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
        for neighbor in self.neighbor_ports:
            print(("[{}] Message sent from Node {} to Node {}").format(time.time(), self.local_port, neighbor))
            node_send_socket.sendto(str(self.dv).encode(), (IP, neighbor))