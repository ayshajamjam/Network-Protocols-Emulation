import socket
from socket import *
import threading
import sys
import json
import time
import ipaddress
from random import *

IP = '127.0.0.1'
buffer_size = 10
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

        self.test = ['O'] * 15
        self.dropped_count = 0
        self.packets_received = 0

        self.window_start = 0
        self.next_available_spot = 0
        self.last_acked_packet = -1

    def nodeListen(self):

        global acked
        
        global start_time

        # Need to declare a new socket bc socket is already being used to send
        node_listen_socket = socket(AF_INET, SOCK_DGRAM)
        node_listen_socket.bind(('', self.self_port))
        
        while True:
            
            self.packets_received += 1

            buffer, sender_address = node_listen_socket.recvfrom(4096)
            buffer = buffer.decode()
            lines = buffer.split('\t')

            # TODO: bc we are using test temporarily, we can later move the 
            # -d -p repeat functionality outside the if conditions

            # Sender got Ack
            if(lines[0] == 'ack'):
                time_received = time.time()
                seqNum = int(lines[1])

                # Sender: determine whether or not to discard ack (simulation)
                if(self.drop_method == '-d'):   # deterministic
                    if(self.drop_value > 0 and (seqNum + 1) % self.drop_value == 0):
                    # if(seqNum == 2 or seqNum == 3 or seqNum == 6):    # for testing
                        lock.acquire()
                        print("Dropping an ack for packet: ", seqNum)
                        self.test[seqNum] = 'X'
                        self.dropped_count += 1
                    else:
                        lock.acquire()
                        # Move the window to most recent ack seq
                        self.window_start = (seqNum + 1) % buffer_size
                        while(self.last_acked_packet < seqNum):
                            self.test[self.last_acked_packet + 1] = 'ACKED: ' + str(self.last_acked_packet + 1)
                            self.sending_buffer[(self.last_acked_packet + 1) % buffer_size] = None
                            self.last_acked_packet += 1
                        print(('[' + str(time_received) + '] ACK packet: {} received, window moves to packet: {}').format(seqNum, self.window_start))
                        print(self.sending_buffer)
                
                print(self.test)
                print(("# Dropped ACKS / # received --- {}/{}: ").format(self.dropped_count, self.packets_received))
                print('\n')
                lock.release()

            # Receiver got message
            else:
                seqNum = int(lines[0])
                data = lines[1]
                ack = 'ack' + '\t' + str(seqNum)

                # Receiver: determine whether or not to discard packet (simulation)
                if(self.drop_method == '-d'):   # deterministic
                    if(self.drop_value > 0 and (seqNum + 1) % self.drop_value == 0):
                        self.test[seqNum] = 'X'
                        self.dropped_count += 1
                    else:
                        self.test[seqNum] = data
                        print(('[' + str(time.time()) + '] packet: {} content: {} received').format(str(seqNum), data))

                print(self.test)
                print(("# Dropped packets / # received --- {}/{}: ").format(self.dropped_count, self.packets_received))

                # TODO: This needs to be moved to else statements
                node_listen_socket.sendto(ack.encode(), (IP, self.peer_port))

    def nodeSend(self):

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

            num = 0
            while num < len(message):
                lock.acquire()
                packet = str(num) + '\t' + message[num]
                # Send message to peer_port
                if(self.next_available_spot - self.window_start < self.window_size):
                    # Insert packet into buffer

                    self.sending_buffer[num % buffer_size] = num
                    print(self.sending_buffer)
                    self.next_available_spot = (self.next_available_spot + 1) % buffer_size
                    node_send_socket.sendto(packet.encode(), (IP, self.peer_port))
                    start_time = float(time.time())
                    print(('Start -- ' + str(num) + ' [' + str(start_time) + '] packet: {} content: {} sent').format(num, message[num]))
                    
                    num += 1
                elif(self.window_size == 5):
                    num = num
                    # print('Cannot send yet, waiting for ACK: ', self.last_acked_packet + 1)
                else:
                    num += 1
                lock.release()