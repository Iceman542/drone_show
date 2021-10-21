#!/usr/bin/python3

# //  ***************************************************************************
# /// @file         Flow_Manager.py
# /// @brief        This module will process the flight management system
# //  ***************************************************************************

import os
import math
import time
import struct
import socket
import threading
import traceback
from threading import Lock
from cflib.crazyflie.log import LogConfig
import cflib.crtp
from cflib.crazyflie.mem import MemoryElement
from collections import deque

from uri_local import g_unity, g_routes, g_params

g_mutex = Lock()
g_end_flight = False
g_begin_flight = False
g_FlowManagerInstances = dict()
g_number_of_drones = 0
g_number_of_drones_ready = 0
g_first_log = True


# ['B' size cmd data 'E']
DRONE_CMD_HEADER = 0x1F
DRONE_CMD_FOOTER = 0xF1
DRONE_CMD_SET_URI = 1
DRONE_CMD_START_POSITION = 2
DRONE_CMD_SET_POSITION = 3
DRONE_CMD_CLOSE = 4

g_drone_comms = None

# NOTE - THIS ISN'T CONNECTED YET
class FlowManagerCommunications():
    def __init__(self):
        self.m_socket = None
        self.m_drone_queue = deque()
        self.m_continue = True

    def open(self, address):
        try:
            self.m_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.m_socket.connect((str(address[0]), int(address[1])))
            t = threading.Thread(target=self.thread, args=(self,))
            t.start()
            print("Unity connected: %s:%d" % (str(address[0]), int(address[1])))
        except:
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
            print(data) """

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

    def close(self):
        self.m_continue = False
        if self.m_socket:
            self.send(DRONE_CMD_CLOSE, bytearray())
            self.m_socket.close()

class FlowManagerClass():
    def __init__(self, scf, uri):
        self.m_uri = uri
        self.m_scf = scf                    # self.m_scf.cf
        self.m_params = g_params[uri]       # self.m_params["uri"]

        self.m_kalman_x = 0
        self.m_kalman_y = 0
        self.m_kalman_z = 0
        self.m_current_yaw = 0
        self.m_end_flight = False

        # SEND URI INDEX & REFERENCE NAME
        self.m_index = self.m_params["index"]
        g_drone_comms.send_uri(self.m_index, uri)

        # SEND STARTING POSITION OF DRONE
        start_pos = self.m_params["start_pos"]
        g_drone_comms.send_start_point(self.m_index, start_pos[0], start_pos[1], start_pos[2])

        try:
            g_mutex.acquire()
            g_FlowManagerInstances[self.m_uri] = self
        finally:
            g_mutex.release()
        time.sleep(1)

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

    @staticmethod
    def run_sequence(self, route):
        global g_mutex
        global g_number_of_drones
        global g_number_of_drones_ready
        global g_end_flight

        x = 0
        y = 1
        z = 2

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

            print(self.m_uri + " online")
            """
            #LED TEST
            print("Testing LED")
            cflib.crtp.init_drivers()
            cf.param.set_value('ring.effect', '2')
            cf.param.set_value('ring.headlightEnable', '1')

            # Get LED memory and write to it
            mem = cf.mem.get_mems(MemoryElement.TYPE_DRIVER_LED)
            if len(mem) > 0:
                mem[0].leds[0].set(r=0, g=100, b=0)
                mem[0].leds[3].set(r=0, g=0, b=100)
                mem[0].leds[6].set(r=100, g=0, b=0)
                mem[0].leds[9].set(r=100, g=100, b=100)
                mem[0].write_data(None)
                print("LED ON")
            """


            # WAIT FOR THE OTHER DRONES
            try:
                g_mutex.acquire()
                g_number_of_drones_ready += 1
            finally:
                g_mutex.release()

            # WAIT FOR ALL DRONES TO SIGNAL READY
            while g_number_of_drones_ready < g_number_of_drones:
                time.sleep(0.01)

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
                g_drone_comms.send_point(self.m_index, x, y, z)

                time.sleep(0.1)
        except:
            traceback.print_exc()

        # LAND
        if cf is not None:
            while self.m_kalman_z > 0.1:
                cf.commander.send_velocity_world_setpoint(0, 0, -0.3, 0)  # vx, vy, vz, yaw
                time.sleep(0.1)
            cf.commander.send_stop_setpoint()
        g_drone_comms.send_point(self.m_index, x, y, 0)
        end_flight()
        print(self.m_uri + " offline")

        if cf is not None:
            logconf.stop()

# CONVERT (x, y, z, mps, time) -> (x, y, z, mps) in 1/10 of a second units
def __expand_route(route):
    full_route = list()
    rate = 0.0
    for r in route:
        t = float(r[3])
        if t == 0:
            t = 10

        rate = r[3] / 10
        if rate > 0.5:
            rate = 0.5

        i = 0.0
        while i < t:
            full_route.append((float(r[0]), float(r[1]), float(r[2]), 0.5))
            i += 0.1
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
    time.sleep(1)
    g_end_flight = True

# *******************************
# TEST CODE
# *******************************

if __name__ == '__main__':
    try:
        try:
            g_drone_comms = FlowManagerCommunications()
            g_drone_comms.open(g_unity)

            i = 0
            g_routes = expand_routes(g_routes)
            begin_flight(len(g_routes))

            threads = list()
            for k, v in g_routes.items():
                fm = FlowManagerClass(None, k)

                x = threading.Thread(target=fm.run_sequence,args=(fm,v,))
                x.start()
                threads.append(x)
                i += 1

            # WAIT FOR THREADS TO COMPLETE
            for x in threads:
                x.join()

            end_flight()
        finally:
            g_drone_comms.close()
    except:
        traceback.print_exc()
    os._exit(0)

# // ////////////////////////////////////////////////////////////////////////////
# // END Flow_Manager.py
# // ////////////////////////////////////////////////////////////////////////////
