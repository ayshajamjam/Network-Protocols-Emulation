# Network Protocols Emulation

## Command-line Instructions:

### GBN:

***Example commands:***

- example_sender: python3 gbnnode.py 1111 2222 5 -p 0.1
- example_receiver: python3 gbnnode.py 2222 1111 5 -p 0.1

### DV:

***Example commands:***

- python3 dvnode.py 1111 2222 .1 3333 .5
- python3 dvnode.py 2222 1111 .1 3333 .2 4444 .8
- python3 dvnode.py 3333 1111 .5 2222 .2 4444 .5
- python3 dvnode.py 4444 2222 .8 3333 .5 last


## Description of Project:

### GBN

**Setup:** In gbnnode.py, I extract the information the user input into the command line, perform some validity checks on the values (port number, drop value, method), and then I create the node using the Node class. The Node class has variables self_port, peer_port, window_size, drop_method (-p, -d), and drop_value. After this, I call on nodeSend to listen for inputs and begin sending to the peer port.

**nodeSend:** In this method, I create a UDP socket for sending, a separate thread for listening, and a separate thread for the timer. I prompt the user for an input which is only valid if it includes ‘send’ first.

I then break the message into single character packets and send each packet out as long as the packet is within the window.

To create the packet, I have a header called ‘data’ (to differentiate it from ack packets), a value for the sequence number, the particular character, and an end flag to mark whether or not this is the last packet being sent (1 = last packet, 0 otherwise).

Before each packet is sent, I add the packet to the sending buffer and update the next_option variable. This keeps track of the next option in the buffer in which I can insert a new character to be sent. The window_start variable keeps track of the first item in the window, and is updated each time an ACK for that sequence number is received.

**nodeListen:** In this method, I create a UDP socket to listen to incoming messages from the peer port. Whenever a packet is received, I increment the counter self.packets_received, which is later used in calculating the loss rate. I then extract the header of the message sent. 

If the header is ‘data’, the ‘receiver’ gets a packet from the ‘sender’ and determines whether or not to drop this packet. If the drop_method is ‘-d’, then it will deterministically drop the packet based on its sequence number. If the sequence number is 2 for example, it will drop every other packet starting from the second character (Ex: hello → h_l_o). If the drop_method is ‘-p’, then it will probabilistically drop the packet. It will determine a random number between 0 and 1 and if that number is less than or equal to the drop value (also between 0 and 1), then the packet is dropped.

If the packet is not dropped, then we check whether or not the last_acked_packet is equal to seqNum-1. If the receiver is expecting a packet that was dropped earlier, it will keep discarding packets until the sender times out and resends that packet. 

If no packets are dropped and the last_acked_packet is one less than the expected packet, then the receiver sends an ack back to the sender and increments its last_acked_packet value.

If the end flag of the data packet is equal to 1, this means that the receiver has gotten the last packet in the message and prints out a summary with the loss rate.

If the header is ‘ack’, the ‘sender’ gets a packet (ACK) from the ‘receiver’ and determines whether or not to drop it. The method to determine this is the same as what was mentioned above for the data packet.

If the sender receives an ACK for a packet it has already received an ACK for (indicating that a data packet was dropped by the receiver), the sender will discard the duplicate packet and the window will not shift, nor will another packet be sent.

Otherwise, if an ACK is received and the sender decides not to drop it, then the timer thread is notified using the Condition object cond, which was declared in nodeSend (see more on the timer below).

The window_start value is then updated to be the seqNum after the last_acked packet, and the values in the sending buffer for the acked packets are set to ‘None’. This ensures that the sending_buffer has enough space in the event that the window wraps around. We increment the last_acked_packet.

If the sequence number of the ack is the same as the length of the message minus 1, then this means that this ack is for the last character in the message. We then print out a summary with the lost rate.

**Timer:** In this method, we receive the Condition object and node_send_socket as parameters. We block the thread using wait, which waits for .5 seconds until another thread (listening thread), notifies it that an ACK has been received.

If no notification has been received, then a timeout occurs and all packets within the window are resent.

### Maintaining the window integrity:

self.window_start = first item at the start of window
self.next_option = next available item in the buffer

If window_start <= next_option, then we ensure that we do not send outside the window_size limit by calculating (self.next-option - self.window_start < self.window_size) before sending out a packet in nodeSend.

If window_start > next_option (wrap around case), then we ensure that we do not send outside the window_size limit by calculating ((self.next-option + buffer_size) - self.window_start < self.window_size) before sending out a packet in nodeSend.

Buffer size: The buffer size is determined by window_size. Buffer_size = window_size + 1. This allows the buffer size to be large enough to fit the entire receiver window without the issue of overlapping.

The sending buffer contains a tuple where the first item is the sequence number and the second is the character.

## Distance Vector

**Setup:** In dvnode.py, I extract the information the user input into the command line, perform some validity checks on the values (port number and loss ratee), and then I create the node using the DvNode class in node2.py. The DvNode object has variables local_port, neighbor_ports, dv, and last. The distance vector, dv, is a dictionary where the key is the port number of a direct neighbor of the node and the value is the loss rate. This is later updated to include non-direct neighbors as well. I then call nodeSend() to start the first round of sending the distance vector, dv, to the neighbors.

**DvNode:** among the variables mentioned above, an object of this class also includes a routing_table, which is a dictionary. The routing_table key is the neighbor port, and the value is a tuple (min_distance, next_hop_node). Here, min_distance is the minimum distance to get from the current node to this neighbor. The constructor only deals with creating the initial routing table for this node and direct neighbors. If the two are direct neighbors, then the next_hop_node value is set to ‘None’. Indirectly connected nodes are later added to the table where their next_hop_node value is also assigned.

**nodeSend:** In this method, I create a UDP socket and a thread for listening. This is done for each individual node. For the last node, where self.last is equal to 1, we send the distance vector to all of its neighbors and increment self.forward_count which keeps track of the number of times this node has forwarded distance vector dv. The message sent includes the local port in the beginning so that the recipient can know which port sent the message.

**nodeListen:** In this method, I create another socket for the listening port. When the node receives a message, the message is split by ‘\n’. The first value is the sender port, and the second value is the distance vector which is converted from a string back to a dictionary and stored in dv_res. I store a copy of this distance vector in old_dv to keep track of whether or not the new information causes a change in this node’s dv. 

We iterate through each key (node) in dv_res. We check if the node currently exists in the routing_table and skip over the key in dv_res associated with the local port. 

If this node exists in this local node’s routing table, then we have to check if the distance in the current dv needs to be updated. We calculate the candidate_dist by adding the distance from the current node to the sender node and the distance sent by the sender node to the neighbor (self.dv[sender_port] + dv_res[node]).

If the candidate_dist is greater than or equal to the current_dist, nothing happens. Otherwise, we update the distance vector value for this particular node to be candidate_dist. We then update the routing_table of the current node.

If the node whose value is being changed to candidate_dist is a direct neighbor of the sender node, then we update the routing table to have the value (candidate_dist, sender_port).

If the node whose value is being changed to candidate_dist is not a direct neighbor of the sender node, meaning, the sender is some hop away, then we update the routing table to have the value (candidate_dist, self.routing_table[sender_port[1]]).

If node does not exist in this local node’s routing table (and is not the local port), then the current node is not directly connected to the node being considered and needs to be added since it is newly reachable.

**Forwarding:** we forward the distance vector if the current node has never forwarded before (self.forward_count == 0) or if the distance vector has changed due to the new information from the sender (self.dv != old_dv). If neither of these cases occur, then the distance vector has not changed and we simply print the routing table.
