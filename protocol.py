#!/usr/bin/python3
import time

class Protocol:

    # RREQ_ID = 0
    # origin_seq = 0
    lifetime = 180

    def __init__(self, originator_adress):
        self.my_adress = originator_adress
        self.RREQ_ID = 0
        self.my_seq = 0
        #dest_seq, hop_count, nexthop, precursor_list, dest_seq_valid, route_valid, lifetime
        timestamp = time.time()
        self.routing_table = {originator_adress: [0, 0, originator_adress, list(), True, True, timestamp]}
        print(self.routing_table)

    # def peer_discovery(self):

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
            if((time.time() - stamp) < 180):
                self.routing_table.get(key)[5] = False
    
    def convert_to_bytes(self, non_byte_input):
        if isinstance(non_byte_input, str):
            return non_byte_input.encode()
        elif isinstance(non_byte_input, int):
            return bytes([non_byte_input])
        else:
            raise ValueError

    def message_handler(self, message):
        print('handling a message')
    
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
        #return bytes(rreq, 'ascii')
        return b"".join([self.convert_to_bytes(message_type),
                        self.convert_to_bytes(uflag),
                        self.convert_to_bytes(hop_count),
                        self.convert_to_bytes(self.RREQ_ID),
                        self.convert_to_bytes(self.my_adress),
                        self.convert_to_bytes(self.my_seq),
                        self.convert_to_bytes(destination_adress),
                        self.convert_to_bytes(seq)])

    def create_RREP(self, originator_adress, destination_adress, originator_seq, destination_seq, previous_hop, rreq_hop_count):
        message_type = 2 #Field 1
        hop_count = 0 #Field 2
        if(destination_adress == self.my_adress):
            print('I am destination')
            # dest_seq = self.my_seq
            if(destination_seq == self.my_seq):
                dest_seq = self.incrementMySeq()
        else:
            print('I am indermidiate')
            dest_seq = self.routing_table.get(destination_adress)[0]
            self.routing_table.get(destination_adress)[4].append(previous_hop)
            self.routing_table[originator_adress] = [originator_seq, rreq_hop_count, previous_hop, list().append(previous_hop), True, True, time.time()]
        self.check_lifetime()
        time_to_live = time.time() - self.routing_table.get(destination_adress)[6]
        rrep = str(message_type) + str(hop_count) + str(originator_adress) + str(destination_adress) + str(dest_seq) + str(time_to_live) + '\r\n'
        return rrep

    def create_RERR(self):
        print('its route error')
    
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

