#!/usr/bin/python3

# //  ***************************************************************************
# /// @file         test.py
# /// @brief        This module will setup the server.
# //  ***************************************************************************

import sys
import struct
import socket
import traceback

DRONE_CMD_HEADER = b'B'
DRONE_CMD_SET_POSITION = 1
DRONE_CMD_FOOTER = b'E'
DRONE_CMD_PACKET_SIZE = 35
DRONE_CMD_DATA_SIZE = 32

class drone_packet():
    def __init__(self):
        self.m_socket = None

    def open(self, address, port):
        self.m_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.m_socket.connect((str(address), int(port)))

    def write(self, cmd, buf):
        data = bytearray()
        data += struct.pack("<B", cmd)
        data += buf
        if len(data) < DRONE_CMD_DATA_SIZE + 1:
            data += bytearray((DRONE_CMD_DATA_SIZE + 1) - len(data))
        data = DRONE_CMD_HEADER + data + DRONE_CMD_FOOTER
        return data

    def read(self, buf):
        if len(buf) != DRONE_CMD_PACKET_SIZE or \
           buf[0] != DRONE_CMD_HEADER or \
           buf[DRONE_CMD_PACKET_SIZE - 1] != DRONE_CMD_FOOTER:
            return None
        return buf[2:DRONE_CMD_DATA_SIZE]

    def send(self, cmd, buf):
        data = self.write(cmd, buf)
        self.m_socket.send(data)

    def recv(self):
        while (True):
            data = bytearray()
            while len(data) < DRONE_CMD_PACKET_SIZE:
                data += self.m_socket.recv(DRONE_CMD_PACKET_SIZE - len(data))
            data = self.read(data)
            data = data.decode('utf-8')
            print(data)

    def close(self):
        self.m_socket.close()

if __name__ == '__main__':
    try:
        packet = drone_packet()
        packet.open("192.168.1.100", 9999)
        packet.send(DRONE_CMD_SET_POSITION, "hello worldxxx".encode('utf-8'))
        #packet.recv()
        packet.close()
    except:
        traceback.print_exc()
        sys.exit(1)
    sys.exit(0)

# // ////////////////////////////////////////////////////////////////////////////
# // END test.py
# // ////////////////////////////////////////////////////////////////////////////
