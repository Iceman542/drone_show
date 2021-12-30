#!/usr/bin/python3

# //  ***************************************************************************
# /// @file         flight_unity.py
# /// @brief        This module will manage the unity logic
# //  ***************************************************************************

import os
import time
import struct
import socket
import threading
import traceback
from collections import deque

from flight_base import base_class

# ['B' size cmd data 'E']
DRONE_CMD_HEADER = 0x1F
DRONE_CMD_FOOTER = 0xF1
DRONE_CMD_SET_URI = 1
DRONE_CMD_START_POSITION = 2
DRONE_CMD_SET_POSITION = 3
DRONE_CMD_CLOSE = 4
DRONE_CMD_SET_LIGHTS = 5

class unity_class(base_class):
    def __init__(self):
        self.m_socket = None
        self.m_drone_queue = deque()
        self.m_continue = True

    def open(self, settings):
        try:
            address = settings["unity"]
            self.m_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.m_socket.connect((str(address[0]), int(address[1])))
            #self.m_socket.recv(1, socket.MSG_DONTWAIT | socket.MSG_PEEK)
            t = threading.Thread(target=self.thread, args=(self,))
            t.start()
            print("Unity connected: %s:%d" % (str(address[0]), int(address[1])))
        except:
            self.m_socket.close()
            print("Unity failed to connect: %s:%d" % (str(address[0]), int(address[1])))
            self.m_continue = False

    """
    def read(self, buf):
        if len(buf) != DRONE_CMD_PACKET_SIZE or \
           buf[0] != DRONE_CMD_HEADER or \
           buf[DRONE_CMD_PACKET_SIZE - 1] != DRONE_CMD_FOOTER:
            return None
        return buf[2:DRONE_CMD_DATA_SIZE]

    def recv(self):
        while (True):
            data = bytearray()
            while len(data) < DRONE_CMD_PACKET_SIZE:
                data += self.m_socket.recv(DRONE_CMD_PACKET_SIZE - len(data))
            data = self.read(data)
            data = data.decode('utf-8')
            print(data) 
    """

    def send(self, cmd, buf):
        data = bytearray()
        data += struct.pack("<BBB", DRONE_CMD_HEADER, len(buf), cmd)
        data += buf
        data += struct.pack("<B", DRONE_CMD_FOOTER)
        if self.m_continue:
            self.m_socket.send(data)

    def send_uri(self, index, uri):
        data = struct.pack("<B", index)
        data += uri.encode('utf-8')
        self.m_drone_queue.appendleft((DRONE_CMD_SET_URI, data))

    def send_start_point(self, index, x, y, z):
        data = struct.pack("<Bfff", index, x, y, z)
        self.m_drone_queue.appendleft((DRONE_CMD_START_POSITION, data))

    def send_point(self, index, x, y, z):
        data = struct.pack("<Bfff", index, x, y, z)
        self.m_drone_queue.appendleft((DRONE_CMD_SET_POSITION, data))

    # lights = (bulb_index,r,g,b)
    def send_lights(self, index, rgb):
        data = struct.pack("<BBBB", index, rgb[0], rgb[1], rgb[2])
        self.m_drone_queue.appendleft((DRONE_CMD_SET_LIGHTS, data))

    @staticmethod
    def thread(self):
        try:
            while self.m_continue:
                if len(self.m_drone_queue):
                    cmd, buf = self.m_drone_queue.pop()
                    self.send(cmd, buf)
                else:
                    time.sleep(0.1)
        except:
            traceback.print_exc()

    def tick(self):
        return True

    def close(self):
        self.m_continue = False
        if self.m_socket:
            self.send(DRONE_CMD_CLOSE, bytearray())
            self.m_socket.close()
            self.m_socket = None
        print("Unity disconnected")

g_unity_class = unity_class()

# *******************************
# TEST CODE
# *******************************
if __name__ == '__main__':
    try:
        from uri_local import g_settings

        g_unity_class.open(g_settings)
        for i in range(0, len(g_settings["uri"])):
            g_unity_class.send_start_point(i, float(g_settings["start_pos"][i][0]), float(g_settings["start_pos"][i][1]), float(g_settings["start_pos"][i][2]))
        time.sleep(3)
        g_unity_class.close()
    except:
        pass
        #traceback.print_exc()
    os._exit(0)

# // ////////////////////////////////////////////////////////////////////////////
# // END flight_unity.py
# // ////////////////////////////////////////////////////////////////////////////
