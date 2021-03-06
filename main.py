#!/usr/bin/python3
import threading
import serial
import time
from datetime import datetime
import os
import socket
import protocol

connected = False
port = '/dev/ttyS0'
baudrate=115200
timeout = 0
clientID = 2



# serial_port = serial.Serial(port, timeout=0)
config = 'AT+CFG=433000000,20,9,10,4,1,0,0,0,0,3000,8,10'
#config = 'AT+CFG=433000000,20,9,12,4,1,0,0,0,0,3000,8,4'

def set_time():
    global origin_time
    origin_time = int(datetime.timestamp(datetime.now()))

def check_timer(time_in_sec):
    if (int(datetime.timestamp(datetime.now())) - origin_time > time_in_sec):
        return False
    else:
        return True


def read_sys_answer():
     loop = True
     while loop:
         if serial_port.in_waiting > 0:
             answer = serial_port.readline().decode('ascii')
             loop = False
     return answer

def write_sys_message(message):
    lock = threading.RLock()
    global serial_port
    if(serial_port.is_open == False):
        serial_port.open()
    with lock:
        answer = ''
        serial_port.write(bytes(str(message) + '\r\n', 'ascii'))
        time.sleep(1)
    
def write_protocol_message(message):
    lock = threading.RLock()
    global serial_port
    if(serial_port.is_open == False):
        serial_port.open()
    with lock:
        answer = ''
        number_bytes = len(message)
        # Writes AT-Command: AT+SEND=number_of_bytes_to_be_sent
        serial_port.write(bytes('AT+SEND='+str(number_bytes)+'\r\n', 'ascii'))
        time.sleep(0.5)
        serial_port.write(message)
        print(str(message))
        time.sleep(1)

def write_text_message(message):
    lock = threading.RLock()
    global serial_port
    if(serial_port.is_open == False):
        serial_port.open()
    with lock:
        serial_port.write(message)
        print(str(message))
        time.sleep(1)

def setup():
    print('Welcome to the chat, ' + socket.gethostname() + '!')
    global serial_port
    global protocol
    protocol = protocol.Protocol(clientID)
    global last_seq_list
    last_seq_list = {13: protocol.get_my_seq}
    # port = input('Enter your Port... \n')
    # port = '/dev/ttyS0'
    # global baudrate
    # global timeout

    # Formatted Settings
    print('')
    print('???----------------------------------------???')
    print('| Settings:                              |')
    print('|----------------------------------------|')
    print('| Port           ' + port + '              |')
    print('| Baudrate       ' + str(baudrate) + '                  |')
    print('| Timeout        ' + str(timeout) + '                       |')
    print('| ClientID       ' + str(clientID) + '                       |')
    print('???----------------------------------------???')

    serial_port = serial.Serial(port, timeout=0, baudrate=115200)
    write_sys_message('AT+RST')
    write_sys_message('AT')
    write_sys_message('AT+ADDR='+str(clientID))
    write_sys_message('AT+ADDR?')
    write_sys_message(config)
    write_sys_message('AT+RX')
    #RREQ TEST
    # write_protocol_message(protocol.create_RREQ(9))

    #Print command List:
    print('')
    print('Command list:')
    print('- write')
    print('- list')
    print('- settings')
    print('- exit')
    print('')

def handle_data(data):
    print(data)

def read_from_port(ser):
    while True:
        exit = False
        reading = ser.readline()
        protocol.check_lifetime()
        if((not reading.startswith(b"AT")) and reading != b""):
            rreq_id = -1
            # partials = reading.split(',', 3)
            # print('Recieved message from ' + partials[1] + ': ' + partials[3])
            #print(reading)
            #print(reading[:11])
            if(reading.startswith(b"LR")):
                previuous_hop = int(reading[5:7])
                payload = reading[11:]
                message_type = int(payload[0])
                ##CASE RREQ
                if(message_type == 1):
                    try:
                        uflag = int(payload[1])
                        hop_count = int(payload[2])
                        rreq_id = int(payload[3])
                        originator_id = int(payload[4])
                        originator_seq = int(payload[5])
                        destination_id = int(payload[6])
                        destination_seq = int(payload[7])
                    except:
                        #print('didnt recieve some bytes')
                        exit = True
                    #print('uflag '+str(uflag) + ', hop_count '+str(hop_count)+ ", rreq_id "+str(rreq_id)+", originator_id "+str(originator_id)+", originator_seq "+str(originator_seq))
                    if(not originator_id == clientID and exit == False and last_seq_list.get(originator_id) != rreq_id):
                        if(protocol.check_routing_table(originator_id) == False):
                            protocol.add_to_routing_table(originator_id, originator_seq, hop_count, previuous_hop, [previuous_hop], True, True)
                        #For me
                        if(destination_id == clientID):
                            print('RREQ for me: ' + 'uflag '+str(uflag) + ', hop_count '+str(hop_count)+ ", rreq_id "+str(rreq_id)+", originator_id "+str(originator_id)+", originator_seq "+str(originator_seq))
                            print('previous hop: ' + str(previuous_hop))
                            write_sys_message('AT+DEST='+str(previuous_hop))
                            write_protocol_message(protocol.create_RREP(originator_id, destination_id, originator_seq, destination_seq, previuous_hop, hop_count))
                        #Not for me
                        else:
                            print('RREQ for ' + str(destination_id) + ': ' + 'uflag '+str(uflag) + ', hop_count '+str(hop_count)+ ", rreq_id "+str(rreq_id)+", originator_id "+str(originator_id)+", originator_seq "+str(originator_seq))
                            #in routing table
                            if(protocol.check_routing_table(destination_id)):
                                #print('in routing table')
                                print('previous hop: ' + str(previuous_hop))
                                write_sys_message('AT+DEST='+str(previuous_hop))
                                write_protocol_message(protocol.create_RREP(originator_id, destination_id, originator_seq, destination_seq, previuous_hop, hop_count))
                            #not in routing table
                            elif(not originator_id == clientID):
                                #print("Not in the table")
                                hop_count += 1
                                print('Forwarded message RREQ from:' + str(originator_id))
                                print(protocol.generate_RREQ(uflag, hop_count, rreq_id, originator_id, originator_seq, destination_id, destination_seq))
                                write_protocol_message(protocol.generate_RREQ(uflag, hop_count, rreq_id, originator_id, originator_seq, destination_id, destination_seq))
                if(message_type == 2):
                    hop_count = int(payload[1])
                    originator_id = int(payload[2])
                    destination_id = int(payload[3])
                    destination_seq = int(payload[4])
                    lifetime = int(payload[5])
                    print('RREP recieved: ' + 'hopcount ' + str(hop_count) + ', originator_id ' + str(originator_id) + ', destiantiod_id ' + str(destination_id) + ', destination_seq ' + str(destination_seq) + ', lifetime ' + str(lifetime))
                    if(protocol.check_routing_table(destination_id) == False):
                        protocol.add_to_routing_table(destination_id, destination_seq, hop_count, previuous_hop, [previuous_hop], True, True)
                    if(originator_id == clientID):
                        print('RREP for me from: ' + str(destination_id))
                        write_sys_message('AT+DEST='+str(previuous_hop))
                        write_protocol_message(protocol.create_RREP_ACK())
                    else:
                        print('RREP not for me from: ' + str(destination_id))
                        if(protocol.check_routing_table(originator_id)):  
                            print('Forwarding RREP to ' + str(originator_id) + ' from ' + str(destination_id))
                            write_sys_message('AT+DEST='+str(originator_id))
                            hop_count += 1
                            write_protocol_message(protocol.generate_RREP(originator_id, destination_id, originator_seq, previuous_hop, hop_count, destination_seq, lifetime))
                if(message_type == 3):
                    destination_count = int(payload[1])
                    unreachable_destination_adress = int(payload[2])
                    unreachable_destination_seq = int(payload[3])

                    for i in range(4, (4 + destination_count) * 2):
                        if(not i % 2):
                            if(protocol.check_routing_table(i)):
                                protocol.routing_table.get(i)[5] = False

                    print('Recieved RERR for ' + str(unreachable_destination_adress))
                    if(protocol.check_routing_table(unreachable_destination_adress)):
                        protocol.routing_table.get(unreachable_destination_adress)[5] = False
                        if(unreachable_destination_adress - protocol.routing_table.get(unreachable_destination_adress)[0] > 0):
                            protocol.routing_table.get(unreachable_destination_adress)[0] = unreachable_destination_seq

                if(message_type == 4):
                    print('Recieved RREP-ACK')
                if(message_type == 5):
                    originator_id = int(payload[1])
                    destination_id = int(payload[2])
                    messag_seq = int(payload[3])
                    message = payload[4:].decode('ascii')
                    #Message for me
                    if(destination_id == clientID):
                        print('Message recieved from ' + str(originator_id) + ': ' + str(message))
                        write_sys_message('AT+DEST=' + str(previuous_hop))
                        print('Sending a TEXT_HOP_ACK to ' + str(previuous_hop))
                        write_protocol_message(protocol.create_HOP_ACK(messag_seq))
                        write_sys_message('AT+DEST=' + str(previuous_hop))
                        print('Sending a TEXT_ACK to ' + str(previuous_hop))
                        write_protocol_message(protocol.create_TEXT_REQ_ACK(originator_id, destination_id, messag_seq))
                    #Message for other node    
                    elif(not destination_id == clientID):
                        print('Message recieved for ' + str(destination_id) + ' from ' + str(originator_id))

                        #send ACK to previous hope
                        write_sys_message('AT+DEST=' + str(previuous_hop))
                        write_protocol_message(protocol.create_HOP_ACK(messag_seq))

                        #check for existense in the routing table
                        if(protocol.check_routing_table(destination_id)):
                            next_hop = protocol.routing_table.get(destination_id)[2]
                            print('Forwarding message to ' + str(next_hop))
                            write_sys_message('AT+DEST=' + str(next_hop))
                            write_protocol_message(protocol.generate_SEND_TEXT_REQ(message_type, originator_id, destination_id, messag_seq, message))
                        else:
                            print('No route!') # ROute discovery when no route table entry
                if(message_type == 6):
                    message_seq = int(payload[1])
                    print('Recieved SHA for message: ' + str(message_seq))
                    #print(reading)
                if(message_type == 7):
                    originator_id = int(payload[1])
                    destination_id = int(payload[2])
                    message_seq = int(payload[3])
                    if(originator_id == clientID):
                        print('Recieved STRA for message: ' + str(message_seq))
                    else:
                        if(protocol.check_routing_table(originator_id)):
                            next_hop = protocol.routing_table.get(originator_id)[2]
                            write_sys_message('AT+DEST=' + str(next_hop))
                            write_protocol_message(protocol.generate_TEXT_REQ_ACK(message_type, originator_id, destination_id, message_seq))
                    #print(reading)
        
                # Add rreq_id to the list of recieve ID from this node
                if(rreq_id > 0):
                    last_seq_list[originator_id] = rreq_id
        time.sleep(1)

# writes a Message
def write_message():
    lock = threading.RLock()
    global serial_port
    if(serial_port.is_open == False):
        serial_port.open()
    with lock:
        dest = 0
        try:
            dest = int(input('Enter the destination: '))
        except:
            print('Invalid input')
        #dest_int = int(dest)
        if(dest == 0):
            return
        exists = protocol.check_routing_table(dest)
        if(exists == True):
            message = input('Your Message:')
            #number_bytes = len(message.encode('ascii'))
            next_hop = protocol.routing_table.get(dest)[2]
            serial_port.write(bytes('AT+DEST='+str(next_hop)+'\r\n', 'ascii'))
            time.sleep(0.5)
            # serial_port.write(bytes('AT+SEND='+str(number_bytes)+'\r\n', 'ascii'))
            # time.sleep(0.5)
            # Writes the payload
            write_protocol_message(protocol.create_SEND_TEXT_REQ(dest, message))
            #serial_port.write(bytes(message + '\r\n', 'ascii'))
        else:
            write_protocol_message(protocol.create_RREQ(dest))
        # Writes AT-Command: AT+SEND=number_of_bytes_to_be_sent
        
        

def readIO():
    loop = True
    while loop:
        command = input("Enter a command \n")
        if(command == "write"):
            write_message()
        if(command == "exit"):
            os._exit(1)
        if(command == "list"):
            print("List of neighbour nodes: ")
        if(command == 'table'):
            print(protocol.print_table())
        else:
            print('Unknown command')
    command = ""

def main():
    setup()
    thread = threading.Thread(target=read_from_port, args=(serial_port,))
    thread.start()
    IOThread = threading.Thread(target = readIO)
    IOThread.start()
    

if __name__ == "__main__":
    main()
