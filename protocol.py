#!/usr/bin/python3
import time
from datetime import datetime

class Protocol:

    # RREQ_ID = 0
    # origin_seq = 0
    lifetime = 180

    def __init__(self, originator_adress):
        self.my_adress = originator_adress #my adress
        self.RREQ_ID = 0 # rreq ID number
        self.my_seq = 0 # seq number
        self.msg_seq = 0 # message seq number
        #dest_seq, hop_count, nexthop, precursor_list, dest_seq_valid, route_valid, lifetime
        timestamp = int(datetime.timestamp(datetime.now()))
        self.routing_table = {originator_adress: [0, 0, originator_adress, list(), True, True, timestamp]}
        print(self.routing_table)

    def print_table(self):
        return str(self.routing_table)

    def get_next_hop(self, id):
        return self.routing_table.get(id)[2]

    def add_to_routing_table(self, destination_adress, dest_seq, hop_count, nexthop, precursor_list, dest_seq_valid, route_valid):
        self.routing_table[destination_adress] = [dest_seq, hop_count, nexthop, precursor_list, dest_seq_valid, route_valid, int(datetime.timestamp(datetime.now()))]
        print('Added ' + str(destination_adress) + 'to my routing table!')

    def get_my_seq(self):
        return self.my_seq

    def check_routing_table(self, id):
        if id in self.routing_table:
            return self.routing_table.get(id)[5] 
        else:
            return False

    def incrementMySeq(self):
        self.my_seq += 1
        self.routing_table.get(self.my_adress)[0] = self.my_seq
        return self.my_seq

    def check_lifetime(self):
        for key in self.routing_table:
            stamp = self.routing_table.get(key)[6]
            result = int(datetime.timestamp(datetime.now()) - stamp)
            print('Result: ' + str(result))
            if(result < 180000):
                self.routing_table.get(key)[5] = False
    
    def convert_to_bytes(self, non_byte_input):
        if isinstance(non_byte_input, str):
            return non_byte_input.encode('ascii')
        elif isinstance(non_byte_input, int):
            return bytes([non_byte_input])
        else:
            raise ValueError

    def message_handler(self, message):
        print('handling a message')

    def generate_RREQ(self, uflag, hop_count, rreq_id, originator_adress, originator_seq, destination_adress, destination_seq):
        message_type = 1 #Field 1
        return b"".join([self.convert_to_bytes(message_type),
                        self.convert_to_bytes(uflag),
                        self.convert_to_bytes(hop_count),
                        self.convert_to_bytes(self.RREQ_ID),
                        self.convert_to_bytes(self.my_adress),
                        self.convert_to_bytes(self.my_seq),
                        self.convert_to_bytes(destination_adress),
                        self.convert_to_bytes(destination_seq)])
    
    def create_RREQ(self, destination_adress):
        message_type = 1 #Field 1
        hop_count = 0 #Field 3
        self.RREQ_ID += 1 #Field 4
        self.incrementMySeq()
        if(destination_adress in self.routing_table):
            uflag = 0
            seq = self.routing_table.get(destination_adress)[0]
        else:
            uflag = 1
            seq = 0
        #rreq = str(message_type) + str(uflag) + str(hop_count) + str(self.RREQ_ID) + str(self.my_adress) + str(self.my_seq) + str(destination_adress) + str(seq) + '\r\n'
        return self.generate_RREQ(uflag, hop_count, self.RREQ_ID, self.my_adress, self.my_seq, destination_adress, seq)
    
    def generate_RREP(self, originator_adress, destination_adress, originator_seq, destination_seq, previous_hop, rreq_hop_count, dest_seq, time_to_live):
        message_type = 2 #Field 1
        hop_count = 0 #Field 2
        return b"".join([self.convert_to_bytes(message_type),
                        self.convert_to_bytes(hop_count),
                        self.convert_to_bytes(originator_adress),
                        self.convert_to_bytes(destination_adress),
                        self.convert_to_bytes(dest_seq),
                        self.convert_to_bytes(time_to_live)])

    def create_RREP(self, originator_adress, destination_adress, originator_seq, destination_seq, previous_hop, rreq_hop_count):
        message_type = 2 #Field 1
        hop_count = 0 #Field 2
        if(destination_adress == self.my_adress):
            print('I am destination')
            # dest_seq = self.my_seq
            if(destination_seq == self.my_seq):
                dest_seq = self.incrementMySeq()
            else:
                dest_seq = self.my_seq
        else:
            print('I am indermidiate')
            dest_seq = self.routing_table.get(destination_adress)[0]
            self.routing_table.get(destination_adress)[3].append(previous_hop)
            self.routing_table[originator_adress] = [originator_seq, rreq_hop_count, previous_hop, list().append(previous_hop), True, True, int(datetime.timestamp(datetime.now()))]
        self.check_lifetime()
        time_to_live = int(datetime.timestamp(datetime.now())) - self.routing_table.get(destination_adress)[6]
        print(time_to_live)
        return self.generate_RREP(originator_adress, destination_adress, originator_seq, destination_seq, previous_hop, rreq_hop_count, dest_seq, time_to_live)

    def create_RERR(self, destination_adress):
        message_type = 3
    
    def create_RREP_ACK(self):
        message_type = 4
        return b"".join([self.convert_to_bytes(message_type), b"\r\n"])

    def generate_SEND_TEXT_REQ(self, message_type, originator_address, destination_adress, message_seq, message):
        return b"".join([self.convert_to_bytes(message_type), self.convert_to_bytes(originator_address), self.convert_to_bytes(destination_adress), self.convert_to_bytes(message_seq), self.convert_to_bytes(message), b"\r\n"])

    def create_SEND_TEXT_REQ(self, destination_adress, message):
        message_type = 5 # Field 1
        originator_address = self.my_adress # Field 2
        self.msg_seq += 1
        return self.generate_SEND_TEXT_REQ(message_type, originator_address, destination_adress, self.msg_seq, message)
    
    def generate_HOP_ACK(self, message_type, message_seq):
        return b"".join([self.convert_to_bytes(message_seq), self.convert_to_bytes(message_seq), b"\r\n"])

    def create_HOP_ACK(self, message_seq):
        message_type = 6
        return self.generate_HOP_ACK(message_type, message_seq)

    def generate_TEXT_REQ_ACK(self, message_type, originator_adress, destination_adress, message_seq):  
        return b"".join([self.convert_to_bytes(message_type), self.convert_to_bytes(originator_adress), self.convert_to_bytes(destination_adress), self.convert_to_bytes(message_seq)])

    def create_TEXT_REQ_ACK(self, originator_address, destination_adress, message_seq):
        message_type = 7
        return self.generate_TEXT_REQ_ACK(message_type, originator_address, destination_adress, message_seq)


    
# def main():
#     protocol = Protocol(3)
#     # message = protocol.create_RREQ(3)
#     # print(str(message, 'ascii'))
#     # message = protocol.create_RREQ(3)
#     # print(str(message, 'ascii'))
#     # message = protocol.create_RREQ(3)
#     # print(str(message, 'ascii'))

# if __name__ == "__main__":
#     main()


