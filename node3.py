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

class CnnNode:
    def __init__(self, local_port, neighbor_ports, dv, last, receive_probes, send_probes):
        self.local_port = local_port
        self.neighbor_ports = neighbor_ports
        self.dv = dv
        self.last = last
        self.routing_table = {} # key: neighbor port, value: tuple: (min_distance, next_hop_node)

        self.receive_probes = receive_probes
        self.send_probes = send_probes

        self.window_size = 5
        self.dropped_count = 0
        self.packets_received = 0

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
            # print("AAAAAAAA: ", self.local_port)
            buffer, sender_address = node_listen_socket.recvfrom(4096)
            # print("BBBBBBBB: ", self.local_port)
            buffer = buffer.decode()
            # print("CCCCCCCC: ", self.local_port)


            split_msg = buffer.split('\n')
            # print(split_msg)
            sender_port = int(split_msg[0])

            # Probe packet
            if (split_msg[1] == "probe"):
                self.packets_received += 1

                print("Probe packet received from ", sender_port)

                random_num = float(randint(1, 100)/100) # (0,1]
                if(random_num <= self.routing_table[sender_port][0]): # probabilistic
                    print(("[{}] packet dropped").format(time.time()))
                    self.dropped_count += 1
                    # print((random_num, self.routing_table[sender_port][0]))
                    print(("{}/{} = {}").format(self.dropped_count, self.packets_received, (self.dropped_count/self.packets_received)))
                else: # send ack
                    node_listen_socket.sendto(str(str(self.local_port)+"\nack").encode(), (IP, sender_port))
                continue
            if(split_msg[1] == 'ack'):
                self.packets_received += 1
                print("Ack received from: ", sender_port)
                continue

            dv_res = ast.literal_eval(split_msg[1])   # converts string containing dv vector to dict
            print(("\n[{}] Message received at Node {} from Node {}").format(time.time(), self.local_port, sender_port))
            print("Message: ", dv_res)

            old_dv = copy.deepcopy(self.dv)
            # print("OLD DV: ", old_dv)

            # Populate routing table
            for node in dv_res:
                if(node != self.local_port and node in self.routing_table.keys()):
                    lock.acquire()
                    current_dist = self.dv[node]
                    candidate_dist = round(self.dv[sender_port] + dv_res[node], 1)
                    # print(node, " >> Node is already in table. ", "current: ", current_dist, ' vs ', "candidate; ", candidate_dist )
                    if(candidate_dist < current_dist):
                        self.dv[node] = candidate_dist

                        if(self.routing_table[sender_port][1] != None):
                            self.routing_table[node] = (candidate_dist, self.routing_table[sender_port][1])
                        else:
                            self.routing_table[node] = (candidate_dist, sender_port)
                        
                        # Remove this neighbor from neighbor_ports to avoid collision
                        # There is an easier way to get to this destination node than directly
                        # if(node in self.neighbor_ports):
                        #     self.neighbor_ports.remove(node)
                        #     print(("Removed {} from neighbor ports").format(node))

                    lock.release()
                elif(node != self.local_port and node not in self.routing_table.keys()):
                    lock.acquire()
                    # print("Neighbor ports: ", self.neighbor_ports)
                    # print(node, " >> Need to add new reachable node: ", node)
                    self.dv[node] = round(self.dv[sender_port] + dv_res[node], 1)
                    self.routing_table[node] = (round(self.dv[sender_port] + dv_res[node], 1), sender_port)
                    lock.release()
                # else:
                #     print(node, " >> This is the local port.")
            
            self.print_routing_table()

            # print("OLD DV: ", old_dv)
            # print("CURRENT DV: ", self.dv)

            # Only forward dv if this node has never forwarded before
            # or if there is a change in the distance vector
            if(self.forward_count == 0):
                # print("First time forwarding")
                # Forward distance vector to neighbors
                self.forward_count += 1
                for neighbor in self.neighbor_ports:
                    print(("[{}] Message sent from Node {} to Node {}").format(time.time(), self.local_port, neighbor))
                    node_listen_socket.sendto(str(str(self.local_port)+'\n'+str(self.dv)).encode(), (IP, neighbor))
            elif(self.dv != old_dv):
                # print("Distance vector has changed")
                self.forward_count += 1
                for neighbor in self.neighbor_ports:
                    print(("[{}] Message sent from Node {} to Node {}").format(time.time(), self.local_port, neighbor))
                    node_listen_socket.sendto(str(str(self.local_port)+'\n'+str(self.dv)).encode(), (IP, neighbor))

            # Probing: send messages to nodes in send_probes
            for node in self.send_probes:
                print(">>PROBING", node)

                # Send packet to peer
                for i in range(0, 10):
                    node_listen_socket.sendto(str(str(self.local_port)+"\nprobe").encode(), (IP, node))
                    print(("[{}] probing packet {} sent from {} to {}").format(time.time(), i, self.local_port, node))

    def nodeSend(self):
        # Create UDP socket
        node_send_socket = socket(AF_INET, SOCK_DGRAM)

        # Multithreading
        listen = threading.Thread(target=self.nodeListen)
        listen.start()

        if(self.last == 1):
            # print("Sending dv to neighbors")
            self.forward_count += 1
            for neighbor in self.neighbor_ports:
                print(("[{}] Message sent from Node {} to Node {}").format(time.time(), self.local_port, neighbor))
                node_send_socket.sendto(str(str(self.local_port)+'\n'+str(self.dv)).encode(), (IP, neighbor))