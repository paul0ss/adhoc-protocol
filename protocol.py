#!/usr/bin/python3
class Protocol:

    # RREQ_ID = 0
    # origin_seq = 0

    def __init__(self, originator_adress):
        self.my_adress = originator_adress
        self.RREQ_ID = 0
        self.origin_seq = 0
        self.routing_table = {originator_adress: [0, 0, originator_adress, None, True, True]}

    # def peer_discovery(self):


    
    def create_RREQ(self, destination_adress):
        message_type = 1 #Field 1
        #get u-flag Field 2
        hop_count = 0 #Field 3
        self.RREQ_ID += 1 #Field 4
        self.origin_seq += 1 #Field 6
        print(self.routing_table.get(self.my_adress)[0])
        self.routing_table.get(self.my_adress)[0] += 1 
        print(self.routing_table.get(self.my_adress)[0])
        print(self.routing_table)
        #get destination_seq Field 7
        rreq = str(message_type) + str(hop_count) + str(self.RREQ_ID) + str(self.my_adress) + str(self.origin_seq) + str(destination_adress) + '\r\n'
        return bytes(rreq, 'ascii')

    def create_RREP(self, originator_adress, destination_adress, originator_seq, destination_seq):
        message_type = 2 #Field 1
        hop_count = 0 #Field 2
        if(destination_adress == self.my_adress):
            print('I am destination')
            if(destination_seq == self.origin_seq):
                self.origin_seq += 1

        else:
            print('I am indermidiate')


    
def main():
    protocol = Protocol(3)
    message = protocol.create_RREQ(2)
    print(str(message, 'ascii'))

if __name__ == "__main__":
    main()


