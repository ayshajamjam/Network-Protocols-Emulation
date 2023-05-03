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

        self.message_length = 0

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
            random_num = float(randint(1, 100)/100) # (0,1]

            # Receiver got data
            if(header == 'data'):
                seqNum = int(lines[1])
                data = lines[2]
                endFlag = int(lines[3])
                # Deterministic packet dropping
                if(self.drop_method == '-d' and self.drop_value > 0 and (seqNum + 1) % self.drop_value == 0):
                # if(self.packets_received < 3 and seqNum == 1):
                    print(">>> Dropping packet: ", seqNum)
                    self.test[(self.last_acked_packet + 1) % buffer_size] = 'X'
                    self.dropped_count += 1
                    # print(("[Summary] {}/{} packets discarded, loss rate = {}%").format(self.dropped_count, self.packets_received, float(self.dropped_count/self.packets_received)))
                elif(self.drop_method == '-p' and random_num <= self.drop_value): # probabilistic
                    print("***Dropping packet: ", seqNum)
                    self.test[(self.last_acked_packet + 1) % buffer_size] = 'X'
                    self.dropped_count += 1
                    # print(("[Summary] {}/{} packets discarded, loss rate = {}%").format(self.dropped_count, self.packets_received, float(self.dropped_count/self.packets_received)))
                elif(self.last_acked_packet != seqNum - 1):
                    print(("[{}] packet: {} content: {} discarded").format(time.time(), seqNum, data))
                    ack = 'ack\t' + str(self.last_acked_packet)
                    node_listen_socket.sendto(ack.encode(), (IP, self.peer_port))
                    print(("[{}] ACK: {} sent, expecting {}").format(time.time(), str(self.last_acked_packet), str(self.last_acked_packet + 1)))
                else:
                    # everything went smoothly, send ack
                    print(("[{}] packet: {} content: {} received").format(time.time(), seqNum, data))
                    ack = 'ack\t' + str(seqNum)
                    self.test[(self.last_acked_packet + 1) % buffer_size] = data
                    self.last_acked_packet += 1
                    node_listen_socket.sendto(ack.encode(), (IP, self.peer_port))
                    print(("[{}] ACK: {} sent, expecting {}").format(time.time(), str(seqNum), str(seqNum + 1)))
                    if(endFlag):
                        print("LAST ACK SENT")
                        print(("[Summary] {}/{} packets discarded, loss rate = {}%").format(self.dropped_count, self.packets_received, float(self.dropped_count/self.packets_received)))
                print(">>> Testing Buffer: ", self.test)
            elif(header == 'ack'):
                seqNum = int(lines[1])
                if(self.drop_method == '-d' and self.drop_value > 0 and (seqNum + 1) % self.drop_value == 0):
                # if(self.drop_method == '-d' and not round2 and (seqNum == 9)):    # for testing
                    lock.acquire()
                    print("***Dropping an ack for packet: ", seqNum, "***")
                    self.test[(self.last_acked_packet + 1) % buffer_size] = 'X'
                    self.dropped_count += 1
                    # print(("[Summary] {}/{} acks discarded, loss rate = {}%").format(self.dropped_count, self.packets_received, float(self.dropped_count/self.packets_received)))
                    print(">>> Testing Buffer: ", self.test)
                    lock.release()
                elif(self.drop_method == '-p' and random_num <= self.drop_value): # probabilistic
                    lock.acquire()
                    print("***Dropping an ack for packet: ", seqNum, "***")
                    self.test[(self.last_acked_packet + 1 )% buffer_size] = 'X'
                    self.dropped_count += 1
                    # print(("[Summary] {}/{} acks discarded, loss rate = {}%").format(self.dropped_count, self.packets_received, float(self.dropped_count/self.packets_received)))
                    print(">>> Testing Buffer: ", self.test)
                    lock.release()
                elif(self.last_acked_packet == seqNum):
                    print(('[{}] ACK packet: {} discarded').format(time.time(), seqNum))
                    print(">>> Testing Buffer: ", self.test)
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
                    print(">>> Testing Buffer: ", self.test)
                    lock.release()
                    if(seqNum == self.message_length - 1):
                        print("LAST CHAR RECEIVED")
                        print(("[Summary] {}/{} acks discarded, loss rate = {}%").format(self.dropped_count, self.packets_received, float(self.dropped_count/self.packets_received)))

                # print(">>> Testing Buffer: ", self.test)

    def timer(self, cond, node_send_socket):
        # global round2

        cond.acquire()
        while True:
            if(self.sending_buffer == [None] * buffer_size):
                continue
            val = cond.wait(.5)
            if val:
                print("Ack received")
            else:
                print("Timeout- resend all packets in window: ", (self.window_start, self.next_option))
                print("Last acked packet: ", self.last_acked_packet)
                # round2 = True
                if(self.window_start < self.next_option):
                    for i in range(self.window_start, self.next_option):
                        endFlag = 0
                        if(i == (self.message_length - 1) % buffer_size):
                            endFlag = 1
                        packet = 'data\t' + str(self.sending_buffer[i][0]) + '\t' + self.sending_buffer[i][1] + '\t' + str(endFlag)
                        node_send_socket.sendto(packet.encode(), (IP, self.peer_port))
                        print(("[{}] packet: {} content: {} REsent").format(time.time(), self.sending_buffer[i][0], self.sending_buffer[i][1]))
                elif(self.window_start > self.next_option):   # deals with wrap around case where window_start is at end of buffer and next_option is at the start
                    for i in range(self.window_start, self.next_option + buffer_size):
                        endFlag = 0
                        if(i == (self.message_length - 1) % buffer_size):
                            endFlag = 1
                        packet = 'data\t' + str(self.sending_buffer[i % buffer_size][0]) + '\t' + self.sending_buffer[i % buffer_size][1] + '\t' + str(endFlag)
                        node_send_socket.sendto(packet.encode(), (IP, self.peer_port))
                        print(("[{}] packet: {} content: {} REsent").format(time.time(), self.sending_buffer[i % buffer_size][0], self.sending_buffer[i % buffer_size][1]))

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
            self.message_length = len(message)

            # Break message into single character packets
            i = 0
            while (i < len(message)) and self.last_acked_packet < len(message) - 1:

                # check if next_option - start_window < window_size
                if((self.next_option >= self.window_start and self.next_option - self.window_start < self.window_size)
                or (self.next_option < self.window_start and (self.next_option + buffer_size) - self.window_start < self.window_size)):

                    if (i == len(message) - 1):
                        print("MAKING PACKET FOR LAST SEND")
                        packet = 'data\t' + str(i) + '\t' + message[i] + '\t' + str(1)
                    else:
                        packet = 'data\t' + str(i) + '\t' + message[i] + '\t' + str(0)
                    
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