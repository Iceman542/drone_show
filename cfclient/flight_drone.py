#!/usr/bin/python3

# //  ***************************************************************************
# /// @file         flight_drone.py
# /// @brief        This module will manage the drone route
# //  ***************************************************************************

import time
import math
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

    # rotation=clockwise or counterclockwise
    # radius=actual radius of the circle
    # lift=z-axis - positive up, negative down
    # start=3,6,9,12 o-clock (on the x-y axis)
    def expand_circle_route(self, pt, t, rotation, radius, lift=0, start=3, rate=0.5):
        if rotation not in ("clockwise", "counterclockwise"):
            raise ValueError("invalid rotation")
        if start not in (3, 6, 9, 12):
            raise ValueError("invalid start")

        t0 = int((t / 4) * 10)  # 1/4 of time
        if t0 == 0:
            raise ValueError("invalid time")

        x = abs(radius)
        xdiff = abs(radius) / t0  # number of entries

        points0 = list()
        for i in range(0, t0):
            y = math.sqrt(abs((radius * radius) - (x * x)))
            points0.append((x, y))
            x -= xdiff

        points1 = list()
        points1.append((0, abs(radius)))
        for i in range(0, t0 - 1):
            px, py = points0[t0 - 1 - i]
            px *= -1.0  # -x
            points1.append((px, py))

        points2 = list()
        for i in range(0, t0):
            px, py = points0[i]
            px *= -1.0  # -x
            py *= -1.0  # -y
            points2.append((px, py))

        points3 = list()
        points3.append((0, -abs(radius)))
        for i in range(0, t0 - 1):
            px, py = points0[t0 - 1 - i]
            py *= -1.0  # -y
            points3.append((px, py))

        if start == 3:
            points = points0 + points1 + points2 + points3  # counterclockwise from 3 o-clock
        elif start == 12:
            points = points1 + points2 + points3 + points0  # counterclockwise from 12 o-clock
        elif start == 9:
            points = points2 + points3 + points0 + points1  # counterclockwise from 9 o-clock
        elif start == 6:
            points = points3 + points0 + points1 + points2  # counterclockwise from 6 o-clock

        if rotation == "clockwise":
            clockwise = list()
            for point in points:
                clockwise.insert(0, point)  # prepend to list (reverse order)
            points = clockwise

        # ADD Z ELEVATION
        zpoints = list()

        pz = float(0)
        zdiff = lift / (t0 * 2)
        for i in range(0, int(t0 * 2)):
            px, py = points[i]
            zpoints.append((px, py, pz))
            pz += zdiff

        zdiff *= -1.0
        for i in range(int(t0 * 2), int(t0 * 4)):
            px, py = points[i]
            zpoints.append((px, py, pz))
            pz += zdiff

        # RELOCATE TO START AT 0,0,0
        rpoints = list()
        xfixup = zpoints[0][0] * -1.0
        for i in range(0, int(t0 * 4)):
            px, py, pz = zpoints[i]
            px += xfixup
            rpoints.append((px, py, pz))

        # RELOCATE TO STARTING POINT
        spoints = list()
        xfixup = pt[0]
        yfixup = pt[1]
        zfixup = pt[2]
        for i in range(0, int(t0 * 4)):
            px, py, pz = rpoints[i]
            px += xfixup
            py += yfixup
            pz += zfixup
            spoints.append((px, py, pz, rate))

        return spoints

    # CONVERT (x, y, z, mps, time, rate) -> (x, y, z, mps) in 1/10 of a second units
    def expand_route(self, route):
        full_route = list()

        x0 = float(0)
        y0 = float(0)
        z0 = float(0)
        for r in route:
            x1 = float(r[0])
            y1 = float(r[1])
            z1 = float(r[2])
            t = float(r[3])
            rate = float(0.5)

            if len(r) == 4:
                i = 0.0
                while i < t:
                    full_route.append((x1, y1, z1, rate))
                    i += 0.1
            else:
                d = r[4]
                if d["type"] == "circle":
                    full_route.extend(self.expand_circle_route((x1, y1, z1), t, rotation=d["rotation"], radius=d["radius"], lift=d["lift"], start=d["start"]))

        return full_route

    def open(self, settings, index, cf, uri, no_route):
        try:
            # LED
            if cf is not None:
                if self.m_led_class:
                    self.m_led_class = led_class()
                    self.m_led_class.open(settings, cf)

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

            if not no_route:
                self.m_running = True
                print(self.m_uri + " online")
            else:
                self.close()
        except:
            traceback.print_exc()
            pass

    def tick_position(self, x, y, z, rate):

        # This shows all log and true values of drone
        print("%f %f %f -> %f %f %f %f - %f" % (self.m_kalman_x, self.m_kalman_y, self.m_kalman_z, x, y, z, rate, self.m_current_yaw))

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
        if vyaw > 0.4:
            vyaw = 5.5
        elif vyaw < -0.4:
            vyaw = -5.5
        else:
            vyaw = 0
        #print("\t%f %f" % (vyaw, self.m_current_yaw))

        # This is the actual command that send the drone the point to move to
        if self.m_cf is not None:
            self.m_cf.commander.send_velocity_world_setpoint(vx, vy, vz, vyaw)  # vx, vy, vz, yaw

    def tick(self):
        global g_end_flight

        try:
            # LED
            if self.m_led_class:
                self.m_led_class.tick()

            if not self.m_running or g_end_flight or self.m_route_index >= len(self.m_route):
                self.close()
                return False

            # ROUTE
            r = self.m_route[self.m_route_index]
            self.m_route_index += 1

            x = r[0]
            y = r[1]
            z = r[2]
            rate = r[3]
            self.tick_position(x, y, z, rate)

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
                self.m_cf.param.set_value('ring.effect', '0')

                # LAND
                print("Landing")
                x = self.m_x
                y = self.m_y
                z = self.m_kalman_z
                while self.m_kalman_z > 0.1:
                    z -= 0.3
                    self.tick_position(x, y, z, 0.5)
                    time.sleep(0.1)

                self.m_cf.commander.send_stop_setpoint()
                self.m_logconf.stop()
                self.m_cf = None
            else:
                time.sleep(2)

            print(self.m_uri + " offline")

            self.m_running = False

if __name__ == '__main__':
    dc = drone_class()
    route = dc.expand_circle_route((1, 0, 1), 5, rotation="counterclockwise", radius=1, lift=0.5, start=3)
    # TEST CODE
    print("end test")

# // ////////////////////////////////////////////////////////////////////////////
# // END flight_drone.py
# // ////////////////////////////////////////////////////////////////////////////
