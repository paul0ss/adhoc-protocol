#!/usr/bin/python3
import threading
import serial
import time
import os
import socket

connected = False
port = '/dev/ttyS0'
baudrate=115200
timeout = 0
clientID = '0002'

# serial_port = serial.Serial(port, timeout=0)
config = 'AT+CFG=433000000,5,9,6,4,1,0,0,0,0,3000,8,10'

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

def setup():
    print('Welcome to the chat, ' + socket.gethostname() + '!')
    global serial_port
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
    print('| ClientID       ' + str(clientID) + '                    |')
    print('└----------------------------------------┘')

    serial_port = serial.Serial(port, timeout=0, baudrate=115200)
    write_sys_message('AT')
    write_sys_message('AT+' + config)
    write_sys_message('AT+RX')

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
        reading = ser.readline().decode('ascii')
        if((not reading.startswith("AT")) and reading != ""):
            partials = reading.split(',', 3)
            print('Recieved message from ' + partials[1] + ': ' + partials[3])
        time.sleep(1)

# writes a Message
def write_message():
    lock = threading.RLock()
    global serial_port
    if(serial_port.is_open == False):
        serial_port.open()
    with lock:
        message = input('Your Message:')
        number_bytes = len(message.encode('ascii'))
        # Writes AT-Command: AT+SEND=number_of_bytes_to_be_sent
        serial_port.write(bytes('AT+SEND='+str(number_bytes)+'\r\n', 'ascii'))
        time.sleep(0.5)
        # Writes the payload
        serial_port.write(bytes(message + '\r\n', 'ascii'))

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
