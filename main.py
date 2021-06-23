#!/usr/bin/python3
import threading
import serial
import time
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
        print('length of message: ' +str(number_bytes))
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
    # port = input('Enter your Port... \n')
    # port = '/dev/ttyS0'
    # global baudrate
    # global timeout

    # Formatted Settings
    print('')
    print('┌----------------------------------------┐')
    print('| Settings:                              |')
    print('|----------------------------------------|')
    print('| Port           ' + port + '              |')
    print('| Baudrate       ' + str(baudrate) + '                  |')
    print('| Timeout        ' + str(timeout) + '                       |')
    print('| ClientID       ' + str(clientID) + '                       |')
    print('└----------------------------------------┘')

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
        reading = ser.readline()
        protocol.check_lifetime()
        if((not reading.startswith(b"AT")) and reading != b""):
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
                    # try:
                    uflag = int(payload[1])
                    hop_count = int(payload[2])
                    rreq_id = int(payload[3])
                    originator_id = int(payload[4])
                    originator_seq = int(payload[5])
                    destination_id = int(payload[6])
                    destination_seq = int(payload[7])
                    # except:
                    #     print('didnt recieve some bytes')
                    #print('uflag '+str(uflag) + ', hop_count '+str(hop_count)+ ", rreq_id "+str(rreq_id)+", originator_id "+str(originator_id)+", originator_seq "+str(originator_seq))
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
                        print('RREQ NOT for me: ' + 'uflag '+str(uflag) + ', hop_count '+str(hop_count)+ ", rreq_id "+str(rreq_id)+", originator_id "+str(originator_id)+", originator_seq "+str(originator_seq))
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
                    write_sys_message('AT+DEST='+str(previuous_hop))
                    write_protocol_message(protocol.create_RREP_ACK())
                    if(originator_id == clientID):
                        print('RREP for me from: ' + str(destination_id))
                    else:
                        print('RREP not for me from: ' + str(destination_id))
                if(message_type == 4):
                    print('Recieved RREP-ACK')
                if(message_type == 5):
                    print('Recieved STR:')
                    originator_id = int(payload[1])
                    destination_id = int(payload[2])
                    messag_seq = int(payload[3])
                    message = payload[4:].decode('ascii')
                    if(destination_id == clientID):
                        print('Message recieved from ' + str(originator_id) + ': ' + str(message))
                        write_sys_message('AT+DEST=' + str(previuous_hop))
                        write_protocol_message(protocol.create_TEXT_REQ_ACK(originator_id, destination_id, messag_seq))
                    elif(not destination_id == clientID):
                        write_sys_message('AT+DEST=' + previuous_hop)
                        write_protocol_message(protocol.create_HOP_ACK(messag_seq))
                        if(protocol.check_routing_table(destination_id)):
                            write_sys_message('AT+DEST=' + protocol.get_next_hop)
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
                    print('Recieved STRA for message: ' + str(message_seq))
                    #print(reading)
        time.sleep(1)

# writes a Message
def write_message():
    lock = threading.RLock()
    global serial_port
    if(serial_port.is_open == False):
        serial_port.open()
    with lock:
        try:
            dest = int(input('Enter the destination: '))
        except:
            print('Invalid input')
        #dest_int = int(dest)
        exists = protocol.check_routing_table(dest)
        if(exists == True):
            message = input('Your Message:')
            number_bytes = len(message.encode('ascii'))
            serial_port.write(bytes('AT+DEST='+str(dest)+'\r\n', 'ascii'))
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
