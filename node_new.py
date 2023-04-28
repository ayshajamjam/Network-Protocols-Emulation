import socket
from socket import *
import threading
import sys
import json
import time
import ipaddress
from random import *
from threading import Condition


IP = '127.0.0.1'
buffer_size = 10
lock = threading.Lock()

def getMessage(input_list):
    message = ""
    for i in range(1, len(input_list)):
        message = message + input_list[i] + " "
    return message.strip()

class Node:
    def __init__(self, self_port, peer_port, window_size, drop_method, drop_value):
        self.self_port = self_port
        self.peer_port = peer_port
        self.window_size = window_size
        self.drop_method = drop_method
        self.drop_value = drop_value
        self.sending_buffer = [None] * buffer_size

    def nodeListen(self):

        # Need to declare a new socket bc socket is already being used to send
        node_listen_socket = socket(AF_INET, SOCK_DGRAM)
        node_listen_socket.bind(('', self.self_port))
        
        while True:

            buffer, sender_address = node_listen_socket.recvfrom(4096)
            buffer = buffer.decode()
            lines = buffer.split('\t')

            header = lines[0]

            if(header == 'data'):
                seqNum = int(lines[1])
                data = lines[2]
                print(("[{}] packet: {} content {} received").format(time.time(), seqNum, data))

                # send ack
                ack = 'ack\t' + str(seqNum)
                node_listen_socket.sendto(ack.encode(), (IP, self.peer_port))
                print(("[{}] ACK: {} sent").format(time.time(), seqNum))
            elif(header == 'ack'):
                seqNum = int(lines[1])
                print(("[{}] ACK: {} received").format(time.time(), seqNum))

    def nodeSend(self):

        # Create UDP socket
        node_send_socket = socket(AF_INET, SOCK_DGRAM)

        # Multithreading
        listen = threading.Thread(target=self.nodeListen)
        listen.start()

        # Time out thread
        timeout_obj = threading.Condition()

        while True:

            # Get input from user
            print("node> ", end="")
            user_input = input()
            input_list = user_input.split()

            if(len(input_list) < 2):
                print("Error: Invalid request")
                continue
            if(input_list[0] != 'send'):
                print("Error: Invalid command. Can only \'send\'")
                continue

            # Retrieve message from input
            message = getMessage(input_list)

            # Break message into single character packets
            for i, char in enumerate(message):
                packet = 'data\t' + str(i) + '\t' + message[i]

                # Add packet to sending buffer
                self.sending_buffer[i % buffer_size] = (i, message[i])

                # Send single character packet to peer
                node_send_socket.settimeout(2)
                node_send_socket.sendto(packet.encode(), (IP, self.peer_port))
                print(("[{}] packet: {} content: {} sent").format(time.time(), i, message[i]))
                print(self.sending_buffer)