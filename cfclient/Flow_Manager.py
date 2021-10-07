#!/usr/bin/python3

# //  ***************************************************************************
# /// @file         Flow_Manager.py
# /// @brief        This module will process the flight management system
# //  ***************************************************************************

import math
import time
import struct
import socket
import traceback
from threading import Lock
from cflib.crazyflie.log import LogConfig
from mpl_toolkits import mplot3d
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

g_mutex = Lock()
g_end_flight = False
g_begin_flight = False
g_FlowManagerInstances = dict()
g_number_of_drones = 0
g_number_of_drones_ready = 0
g_first_log = True

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
    def __init__(self, scf, params, uri):
        self.m_scf = scf                # self.m_scf.cf
        self.m_params = params          # self.m_params["uri"]

        if scf is None:
            self.m_uri = uri
        else:
            self.m_uri = scf.cf.link_uri
        self.m_kalman_x = 0
        self.m_kalman_y = 0
        self.m_kalman_z = 0
        self.m_current_yaw = 0
        self.m_end_flight = False
        try:
            g_mutex.acquire()
            g_FlowManagerInstances[self.m_uri] = self
            print(self.m_uri + " online")
        finally:
            g_mutex.release()

    @staticmethod
    def log_stab_callback(timestamp, data, logconf):
        global g_first_log
        try:
            uri = logconf.cf.link_uri

            # Use this to debug to see battery print
            # print('[%d][%s]: %s' % (timestamp, logconf.name, data))

            if uri in g_FlowManagerInstances:
                fm = g_FlowManagerInstances[uri]
                fm.m_current_yaw = data["stabilizer.yaw"]
                fm.m_kalman_x = data["kalman.stateX"]
                fm.m_kalman_y = data["kalman.stateY"]
                fm.m_kalman_z = data["kalman.stateZ"]
                if data["pm.state"] != 0:
                    print(uri + ' is low battery')
                    fm.m_end_flight = True
        except:
            traceback.print_exc()

    def run_sequence(self, route):
        global g_mutex
        global g_number_of_drones
        global g_number_of_drones_ready
        global g_end_flight
        global ax
        global fig

        try:
            if self.m_scf is None:
                cf = None
            else:
                cf = self.m_scf.cf

            if cf is not None:
                # Logging - this creates a thread for each drone
                logconf = LogConfig(name='Stabilizer', period_in_ms=100)
                logconf.add_variable('pm.batteryLevel', 'float')
                logconf.add_variable('pm.state', 'int8_t')
                logconf.add_variable('stabilizer.yaw', 'float')
                logconf.add_variable('kalman.stateX', 'float')
                logconf.add_variable('kalman.stateY', 'float')
                logconf.add_variable('kalman.stateZ', 'float')
                cf.log.add_config(logconf)
                logconf.data_received_cb.add_callback(self.log_stab_callback)
                logconf.start()

            # WAIT FOR THE OTHER DRONES
            try:
                g_mutex.acquire()
                g_number_of_drones_ready += 1
            finally:
                g_mutex.release()

            # WAIT FOR ALL DRONES TO SIGNAL READY
            while g_number_of_drones_ready < g_number_of_drones:
                time.sleep(0.001)

            # START FLIGHT
            for r in route:
                # CHECK FOR CANCEL
                if g_end_flight or self.m_end_flight:
                    break

                x = r[0]
                y = r[1]
                z = r[2]
                rate = r[3]
                vx = 0
                vy = 0
                vz = 0

                # This shows all log and true values of drone
                #print("%f %f %f -> %f %f %f %f - %f" % (self.m_kalman_x, self.m_kalman_y, self.m_kalman_z, x, y, z, rate, self.m_current_yaw))

                # PROCESS UP
                vx = x - self.m_kalman_x
                if vx > rate:
                    vx = rate
                if vx < -rate:
                    vx = -rate
                vy = y - self.m_kalman_y
                if vy > rate:
                    vy = rate
                if vy < -rate:
                    vy = -rate
                vz = z - self.m_kalman_z
                if vz > rate:
                    vz = rate
                if vz < -rate:
                    vz = -rate

                vyaw = self.m_current_yaw
                if vyaw > 0.5:
                    vyaw = 5.5
                elif vyaw < -0.5:
                    vyaw = -5.5
                else:
                    vyaw = 0

                #print("%f" % vyaw)

                # This is the actual command that send the drone the point to move to
                if cf is not None:
                    cf.commander.send_velocity_world_setpoint(vx, vy, vz, vyaw)  # vx, vy, vz, yaw

                time.sleep(0.1)
        except:
            traceback.print_exc()

        # LAND
        if cf is not None:
            while self.m_kalman_z > 0.1:
                cf.commander.send_velocity_world_setpoint(0, 0, -0.3, 0)  # vx, vy, vz, yaw
                time.sleep(0.1)
            if self.m_scf:
                cf.commander.send_stop_setpoint()
        print(self.m_uri + " offline")

        if cf is not None:
            logconf.stop()

def animate(x, y, z):
    print("animating")
    ax.clear()
    ax.plot(x, y, z)


    # updating data values
    ax.set_xdata(x)
    ax.set_ydata(y)
    ax.set_zdata(z)

    # drawing updated values
    fig.canvas.draw()

    # This will run the GUI event
    # loop until all UI events
    # currently waiting have been processed
    fig.canvas.flush_events()

# CONVERT (x, y, z, mps, time) -> (x, y, z, mps) in 1/10 of a second units
def __expand_route(route):
    full_route = list()
    rate = 0.0
    for r in route:
        t = r[3] * 10   # convert to 1/10 of a second
        if t == 0:
            t = 10

        rate = r[3] / 10
        if rate < 0.5:
            rate = 0.5

        for i in range(0, t):
            full_route.append((float(r[0]), float(r[1]), float(r[2]), 0.5))
    return full_route

def expand_routes(routes):
    for k, v in routes.items():
        routes[k] = __expand_route(v)
    return routes

def begin_flight(number_of_drones):
    global g_number_of_drones
    print("Begin Flight")
    g_number_of_drones = number_of_drones

def end_flight():
    global g_end_flight
    if not g_end_flight:
        print("End Flight")
    g_end_flight = True

# *******************************
# TEST CODE
# *******************************

# (x_meters, y_meters, z_meters, time_seconds)
g_test_route0 = [
    (0, 0, 1, 2),   # up
    (0, 0, 1, 2),   # hover
    (1, 0, 1, 2),   # forward6
]
g_test_route1 = [
    (0, 0, 1, 1),  # go up
    (1, 0, 1, 1),  # go right
    (1, 1, 1, 1),  # go forward
    (1, 1, 0, 1),  # land6
]
g_test_routes = {"g_test_route0": g_test_route0}

if __name__ == '__main__':
    try:
        i = 0
        g_test_routes = expand_routes(g_test_routes)
        begin_flight(1)
        for k, v in g_test_routes.items():
            fm = FlowManagerClass(None, None, "DRONE %d" % i)
            i += 1
            fm.run_sequence(v)
        end_flight()
    except:
        traceback.print_exc()

# // ////////////////////////////////////////////////////////////////////////////
# // END Flow_Manager.py
# // ////////////////////////////////////////////////////////////////////////////
