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
round2 = False

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

        self.test = ['O'] * buffer_size
        self.packets_received = 0
        self.dropped_count = 0
        self.last_acked_packet = -1

        self.window_start = 0
        self.next_option = 0

    def nodeListen(self, cond):


        # Need to declare a new socket bc socket is already being used to send
        node_listen_socket = socket(AF_INET, SOCK_DGRAM)
        node_listen_socket.bind(('', self.self_port))
        
        while True:

            self.packets_received += 1

            buffer, sender_address = node_listen_socket.recvfrom(4096)
            buffer = buffer.decode()
            lines = buffer.split('\t')

            header = lines[0]

            # Receiver got data
            if(header == 'data'):
                seqNum = int(lines[1])
                data = lines[2]
                # Deterministic packet dropping
                if(self.drop_method == '-d'):
                    if(self.packets_received < 3 and seqNum == 1):
                        print(">>> Dropping packet: ", seqNum)
                        self.test[seqNum % buffer_size] = 'X'
                        self.dropped_count += 1
                        print(("# Dropped ACKS / # received --- {}/{}: ").format(self.dropped_count, self.packets_received))
                    elif(self.last_acked_packet != seqNum - 1):
                        print(("[{}] packet: {} content: {} discarded").format(time.time(), seqNum, data))
                        ack = 'ack\t' + str(self.last_acked_packet)
                        node_listen_socket.sendto(ack.encode(), (IP, self.peer_port))
                        print(("[{}] ACK: {} sent, expecting {}").format(time.time(), str(self.last_acked_packet), str(self.last_acked_packet + 1)))
                    else:
                        # everything went smoothly, send ack
                        print(("[{}] packet: {} content: {} received").format(time.time(), seqNum, data))
                        ack = 'ack\t' + str(seqNum)
                        self.test[seqNum % buffer_size] = data
                        self.last_acked_packet += 1
                        node_listen_socket.sendto(ack.encode(), (IP, self.peer_port))
                        print(("[{}] ACK: {} sent, expecting {}").format(time.time(), str(seqNum), str(seqNum + 1)))
                print(">>> Testing Buffer: ", self.test)
            elif(header == 'ack'):
                seqNum = int(lines[1])

                if(self.drop_method == '-d'):   # deterministic
                    if(not round2 and (seqNum == -1)):    # for testing
                        print("***Dropping an ack for packet: ", seqNum, "***")
                        self.test[seqNum % buffer_size] = 'X'
                        self.dropped_count += 1
                        print(("# Dropped ACKS / # received --- {}/{}: ").format(self.dropped_count, self.packets_received))
                    elif(self.last_acked_packet == seqNum):
                        print(('[{}] ACK packet: {} discarded').format(time.time(), seqNum))
                    else:
                        cond.acquire()
                        cond.notify()
                        cond.release()

                        lock.acquire()
                        # Move the window to most recent ack seq
                        self.window_start = (seqNum + 1) % buffer_size
                        print(('[{}] ACK packet: {} received, window moves to packet: {}').format(time.time(), seqNum, self.window_start))
                        while(self.last_acked_packet < seqNum):
                            self.test[(self.last_acked_packet + 1) % buffer_size] = 'ack: ' + str(self.last_acked_packet + 1)
                            self.sending_buffer[(self.last_acked_packet + 1) % buffer_size] = None
                            print(self.sending_buffer)
                            self.last_acked_packet += 1
                        print(self.window_start, ' ', self.next_option)
                        lock.release()
                print(">>> Testing Buffer: ", self.test)

    def timer(self, cond, node_send_socket):
        global round2

        cond.acquire()
        while True:
            if(self.sending_buffer == [None] * buffer_size):
                continue
            val = cond.wait(3)
            if val:
                print("Ack received")
            else:
                print("Timeout- resend all packets in window")
                print("Last acked packet: ", self.last_acked_packet)
                round2 = True
                for i in range(self.window_start, self.next_option):
                    packet = 'data\t' + str(i) + '\t' + self.sending_buffer[i][1]
                    node_send_socket.sendto(packet.encode(), (IP, self.peer_port))
                    print(("[{}] packet: {} content: {} REsent").format(time.time(), i, self.sending_buffer[i][1]))
        cond.release()
        
    def nodeSend(self):
        print("Hello")

        # Condition object
        cond = threading.Condition()

        # Create UDP socket
        node_send_socket = socket(AF_INET, SOCK_DGRAM)

        # Multithreading
        listen = threading.Thread(target=self.nodeListen, args=(cond,))
        listen.start()

        # Time out thread
        timeout = threading.Thread(target=self.timer, args=(cond, node_send_socket))
        timeout.start()

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
            i = 0
            while (i < len(message)) and self.last_acked_packet < len(message) - 1:

                # check if next_option - start_window < window_size
                if(self.next_option - self.window_start < self.window_size):

                    packet = 'data\t' + str(i) + '\t' + message[i]
                    
                    # Add packet to sending buffer
                    lock.acquire()
                    self.sending_buffer[i % buffer_size] = (i, message[i])  # TODO: fix
                    self.next_option = (self.next_option + 1) % buffer_size
                    lock.release()

                    # Send single character packet to peer
                    node_send_socket.sendto(packet.encode(), (IP, self.peer_port))
                    print(("[{}] packet: {} content: {} sent").format(time.time(), i, message[i]))

                    print(self.sending_buffer)
                    print(self.window_start, ' ', self.next_option)

                    i += 1