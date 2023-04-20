import socket
from socket import *
import threading
import sys
import json
import time
import ipaddress

IP = '127.0.0.1'
buffer_size = 10
window_filled = 0
lock = threading.Lock()

acked = {}
start_time = 0

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

        global window_filled
        global acked
        
        # Need to declare a new socket bc socket is already being used to send
        node_listen_socket = socket(AF_INET, SOCK_DGRAM)
        node_listen_socket.bind(('', self.self_port))

        while True:

            buffer, sender_address = node_listen_socket.recvfrom(4096)
            buffer = buffer.decode()
            lines = buffer.split('\t')

            # Ack
            if(lines[0] == 'ack'):
                seqNum = lines[1]

                print('Stop -- ' + str(seqNum) + ' [' + str(time.time()) + ']')
                lock.acquire()
                acked[int(seqNum)] = 1
                window_filled -= 1
                self.sending_buffer[int(seqNum) % buffer_size] = None
                print(('[' + str(start_time) + '] ACK packet: {} received, window moves to packet: {}').format(seqNum, str(int(seqNum) + 1)))
                print(self.sending_buffer)
                lock.release()
            # Message
            else:
                seqNum = lines[0]
                data = lines[1]

                print(('[' + str(start_time) + '] packet: {} content: {} received').format(seqNum, data))

                ack = 'ack' + '\t' + seqNum
                node_listen_socket.sendto(ack.encode(), (IP, self.peer_port))


    def nodeSend(self):

        global window_filled
        global start_time

        # Create UDP socket
        node_send_socket = socket(AF_INET, SOCK_DGRAM)

        # Multithreading
        listen = threading.Thread(target=self.nodeListen)
        listen.start()

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

            # Construct packets, send
            print(self.sending_buffer)
            num = 0
            while num < len(message):
                packet = str(num) + '\t' + message[num]
                
                # Send message to peer_port
                if(window_filled < self.window_size):
                    # Insert packet into buffer
                    lock.acquire()
                    self.sending_buffer[num % buffer_size] = message[num]
                    print(self.sending_buffer)
                    window_filled += 1
                    lock.release()
                    node_send_socket.sendto(packet.encode(), (IP, self.peer_port))
                    start_time = time.time()
                    print(('Start -- ' + str(num) + ' [' + str(start_time) + '] packet: {} content: {} sent').format(num, message[num]))
                    num += 1
                elif(self.window_size == 5):
                    print('Cannot send yet')
                else:
                    num += 1