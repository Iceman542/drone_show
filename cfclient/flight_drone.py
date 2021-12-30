#!/usr/bin/python3

# //  ***************************************************************************
# /// @file         flight_drone.py
# /// @brief        This module will manage the drone route
# //  ***************************************************************************

import time
import traceback
from cflib.crazyflie.log import LogConfig

from flight_led import led_class
from flight_base import base_class, g_begin_flight, g_end_flight, g_drone_entity
from flight_unity import g_unity_class

class drone_class(base_class):
    def __init__(self):
        self.m_running = False
        self.m_kalman_x = 0
        self.m_kalman_y = 0
        self.m_kalman_z = 0
        self.m_current_yaw = 0
        self.m_index = None
        self.m_cf = None
        self.m_led_class = None
        self.m_x = 0
        self.m_y = 0

    @staticmethod
    def log_stab_callback(timestamp, data, logconf):
        global g_end_flight

        try:
            # Use this to debug to see battery print
            # print('[%d][%s]: %s' % (timestamp, logconf.name, data))

            uri = logconf.cf.link_uri
            if uri in g_drone_entity:
                self = g_drone_entity[uri]

                self.m_current_yaw = data["stabilizer.yaw"]
                self.m_kalman_x = data["kalman.stateX"]
                self.m_kalman_y = data["kalman.stateY"]
                self.m_kalman_z = data["kalman.stateZ"]
                if data["pm.state"] != 0:
                    print(uri + ' is low battery')
                    g_end_flight = True
        except:
            traceback.print_exc()

    # CONVERT (x, y, z, mps, time) -> (x, y, z, mps) in 1/10 of a second units
    def expand_route(self, route):
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

    def open(self, settings, index, cf, uri):
        try:
            # SETUP LIGHTS
            self.m_index = index
            self.m_cf = cf
            self.m_uri = uri

            self.m_route = self.expand_route(settings["route"][index])
            self.m_route_index = 0

            # SEND URI INDEX & REFERENCE NAME
            g_unity_class.send_uri(self.m_index, self.m_uri)

            # SEND STARTING POSITION OF DRONE
            start_pos = settings["start_pos"][index]
            g_unity_class.send_start_point(self.m_index, start_pos[0], start_pos[1], start_pos[2])
            time.sleep(2)

            if self.m_cf is not None:
                # LED
                if self.m_led_class:
                    self.m_led_class = led_class()
                    self.m_led_class.open(settings, self.m_cf)

                # Flight Controller
                self.m_cf.param.set_value('kalman.initialX', 0)
                self.m_cf.param.set_value('kalman.initialY', 0)
                self.m_cf.param.set_value('kalman.initialZ', 0)

                self.m_cf.param.set_value('kalman.resetEstimation', '1')
                time.sleep(0.1)
                self.m_cf.param.set_value('kalman.resetEstimation', '0')
                time.sleep(2)

                # Logging - this creates a thread for each drone
                self.m_logconf = LogConfig(name='Stabilizer', period_in_ms=100)
                self.m_logconf.add_variable('pm.batteryLevel', 'float')
                self.m_logconf.add_variable('pm.state', 'int8_t')
                self.m_logconf.add_variable('stabilizer.yaw', 'float')
                self.m_logconf.add_variable('kalman.stateX', 'float')
                self.m_logconf.add_variable('kalman.stateY', 'float')
                self.m_logconf.add_variable('kalman.stateZ', 'float')
                cf.log.add_config(self.m_logconf)
                self.m_logconf.data_received_cb.add_callback(self.log_stab_callback)
                self.m_logconf.start()

            print(self.m_uri + " online")
        except:
            # traceback.print_exc()
            pass

        self.m_running = True

    def tick(self):
        global g_end_flight

        try:
            if not self.m_running or g_end_flight or self.m_route_index >= len(self.m_route):
                self.close()
                return False

            # LED
            if self.m_led_class:
                self.m_led_class.tick()

            # ROUTE
            r = self.m_route[self.m_route_index]
            self.m_route_index += 1

            x = r[0]
            y = r[1]
            z = r[2]
            rate = r[3]

            # This shows all log and true values of drone
            # print("%f %f %f -> %f %f %f %f - %f" % (self.m_kalman_x, self.m_kalman_y, self.m_kalman_z, x, y, z, rate, self.m_current_yaw))

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
            if self.m_cf is not None:
                self.m_cf.commander.send_velocity_world_setpoint(vx, vy, vz, vyaw)  # vx, vy, vz, yaw

            g_unity_class.send_point(self.m_index, x, y, z)

            self.m_x = x
            self.m_y = y
        except:
            self.m_running = False

        return self.m_running

    def close(self):
        if self.m_running:
            # LED
            if self.m_led_class:
                self.m_led_class.close()

            # UNITY
            g_unity_class.send_point(self.m_index, self.m_x, self.m_y, 0)

            # DRONE
            if self.m_cf is not None:
                # LAND
                while self.m_kalman_z > 0.1:
                    self.m_cf.commander.send_velocity_world_setpoint(0, 0, -0.3, 0)  # vx, vy, vz, yaw
                    time.sleep(0.1)
                self.m_cf.commander.send_stop_setpoint()
                self.m_cf.param.set_value('ring.effect', '0')

                self.m_logconf.stop()
                self.m_cf = None
            else:
                time.sleep(2)

            print(self.m_uri + " offline")

            self.m_running = False

# // ////////////////////////////////////////////////////////////////////////////
# // END flight_drone.py
# // ////////////////////////////////////////////////////////////////////////////
