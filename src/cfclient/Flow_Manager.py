#!/usr/bin/python3

# //  ***************************************************************************
# /// @file         Flow_Manager.py
# /// @brief        This module will process the flight management system
# //  ***************************************************************************

import time
import struct
import socket
import traceback
from threading import Lock

g_mutex = Lock()
g_end_flight = False
g_begin_flight = False
g_FlowManagerInstances = dict()
g_number_of_drones_ready = 0

DRONE_CMD_HEADER = b'B'
DRONE_CMD_SET_POSITION = 1
DRONE_CMD_FOOTER = b'E'
DRONE_CMD_PACKET_SIZE = 35
DRONE_CMD_DATA_SIZE = 32

g_drone_comms = None

# NOTE - THIS ISN'T CONNECTED YET
class FlowManagerCommunications():
    def __init__(self):
        global g_drone_comms
        self.m_socket = None
        g_drone_comms = self

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

class FlowManagerClass():
    def __init__(self, scf, input_uri):
        self.m_uri = input_uri
        self.m_scf = scf                # self.m_scf.cf
        self.m_current_yaw = 0
        self.m_end_flight = False
        try:
            g_mutex.acquire()
            g_FlowManagerInstances[self.m_uri] = self
            print(self.m_uri + " online")
        finally:
            g_mutex.release()

    def run_sequence(self, route):
        global g_begin_flight
        global g_end_flight
        global g_number_of_drones_ready
        try:
            current_pos = (0, 0, 0)

            # WAIT FOR THE OTHER DRONES
            try:
                g_mutex.acquire()
                g_number_of_drones_ready += 1
            finally:
                g_mutex.release()
            if not g_begin_flight:
                time.sleep(0.001)

            # START FLIGHT
            for r in route:
                # CHECK FOR CANCEL
                if g_end_flight or self.m_end_flight:
                    break

                # CALCULATE CHANGE FROM CURRENT POSITION
                x = round(r[0] - current_pos[0], 2)
                y = round(r[1] - current_pos[1], 2)
                z = round(r[2] - current_pos[2], 2)
                current_pos = r

                # CALCULATE YAW - only move by half the error
                if self.m_current_yaw > 0:
                    yaw = -(self.m_current_yaw / 2)
                else:
                    yaw = self.m_current_yaw / 2

                print("%f %f %f\n", current_pos[0], current_pos[1], current_pos[2])
                if self.m_scf:

                    self.m_scf.cf.commander.send_hover_setpoint(
                        current_pos[0], current_pos[1], current_pos[2], current_pos[2])

                time.sleep(0.1)
        except:
            traceback.print_exc()

        # LAND
        while current_pos[2] > 0:
            self.m_scf.cf.commander.send_hover_setpoint(0, 0, 0, -0.1)
            current_pos[2] -= 0.1
        if self.m_scf:
            self.m_scf.cf.commander.send_stop_setpoint()

def __expand_diff(a, b, t):
    if a > b:
        return round((a - b) / t, 2)
    return round(-((b - a) / t), 2)

# CONVERT (x, y, z, time) -> (x, y, z) in 1/10 of a second units
def __expand_route(route):
    full_route = list()
    x = 0.0
    y = 0.0
    z = 0.0
    for r in route:
        t = r[3] * 10    # convert to 1/10 of a second
        if t == 0:
            t = 10
        diff_x = __expand_diff(r[0], x, t)
        diff_y = __expand_diff(r[1], y, t)
        diff_z = __expand_diff(r[2], z, t)
        for i in range(0, t):
            x = round(x + diff_x, 2)
            y = round(y + diff_y, 2)
            z = round(z + diff_z, 2)
            full_route.append((x, y, z))
    return full_route

def expand_routes(routes):
    new_routes = list()
    for r in routes:
        new_routes.append(__expand_route(r))
    return new_routes

def update_current_yaw(uri, yaw):
    try:
        if uri in g_FlowManagerInstances:
            g_FlowManagerInstances[uri].m_current_yaw = yaw
    except:
        pass

def begin_flight(number_of_drones):
    global g_begin_flight
    global g_number_of_drones_ready

    print("Begin Flight")
    time.sleep(0.5)

    """
        THIS NEEDS TO CONNECT TO EACH DRONE
    """

    # WAIT FOR ALL DRONES TO SIGNAL READY
    #while g_number_of_drones_ready < number_of_drones:
    #    time.sleep(0.5)
    g_begin_flight = True

def end_flight(uri=None):
    global g_end_flight
    # ONLY END FOR THIS DRONE
    if uri is not None:
        if uri in g_FlowManagerInstances:
            g_FlowManagerInstances[uri].m_end_flight = True
    # END FOR ALL DRONES
    else:
        if not g_end_flight:
            print("End Flight")
        g_end_flight = True

# *******************************
# TEST CODE
# *******************************

# (x_meters, y_meters, z_meters, time_seconds)
g_test_route1 = [
    (0, 0, 1, 2),  # go up
    # (1, 0, 1, 1),   # go right
    # (1, 1, 1, 1),   # go forward
    (0, 0, 0, 2),  # land
]
g_test_route2 = [
    (0, 0, 1, 1),  # go up
    (1, 0, 1, 1),  # go right
    (1, 1, 1, 1),  # go forward
    (1, 1, 0, 1),  # land
]
g_test_routes = [g_test_route1, g_test_route2]

if __name__ == '__main__':
    try:
        g_test_routes = expand_routes(g_test_routes)
        begin_flight(1)  # MANUALLY CHANGE THIS NUMBER
        for route in g_test_routes:
            uri = "radio://0/80/2M/E7E7E7E7E5"
            fm = FlowManagerClass(None, uri)
            fm.run_sequence(route)
        end_flight()
    except:
        traceback.print_exc()

# // ////////////////////////////////////////////////////////////////////////////
# // END Flow_Manager.py
# // ////////////////////////////////////////////////////////////////////////////