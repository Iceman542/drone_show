import os
import logging
import time
import threading
import traceback
import argparse

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.swarm import CachedCfFactory, Swarm

from flight_base import g_begin_flight, g_end_flight, g_drone_entity
from flight_music import g_music_class
from flight_unity import g_unity_class
from uri_local import g_settings
import flight_drone

g_mutex = threading.Lock()
g_drone_count = 0
g_args = None

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

def parse_arguments():
    global g_args
    parser = argparse.ArgumentParser()
    parser.add_argument('--no_unity', dest='no_unity', action='store_true')
    parser.add_argument('--no_music', dest='no_music', action='store_true')
    parser.add_argument('--no_route', dest='no_route', action='store_true')
    parser.add_argument('--no_led', dest='no_led', action='store_true')
    g_args = parser.parse_args()
    return g_args

# This is a kill thread, by pressing ENTER
def thread_function():
    global g_end_flight

    input()                             # WAIT FOR ENTER
    print("ENTER pressed - waiting 5 seconds to cleanup")
    g_end_flight = True

def thread_function2(flight_time):
    global g_end_flight
    try:
        try:
            flight_time = float(flight_time)

            # WAIT FOR DRONES TO GET READY
            while not g_begin_flight:
                time.sleep(.1)

            while not g_end_flight and flight_time > 0:
                if g_music_class:
                    g_music_class.tick()
                g_unity_class.tick()
                time.sleep(.1)
                flight_time -= 0.1
        finally:
            g_end_flight = True
            if g_music_class:
                g_music_class.close()
            g_unity_class.close()
    except:
        traceback.print_exc()

def reset_estimator(scf):
    try:
        cf = scf.cf

        # CLEAR LED
        cf.param.set_value('ring.effect', '0')

        cf.param.set_value('kalman.initialX', 0)
        cf.param.set_value('kalman.initialY', 0)
        cf.param.set_value('kalman.initialZ', 0)

        cf.param.set_value('kalman.resetEstimation', '1')
        time.sleep(0.1)
        cf.param.set_value('kalman.resetEstimation', '0')
        time.sleep(2)
    except:
        pass

#def drone_main(scf, index):
def drone_main(scf):
    global g_begin_flight
    global g_drone_entity
    global g_drone_count

    try:
        cf = scf.cf
        uri = cf.link_uri
        settings = g_settings["drones"][uri]
        index = settings["index"]

        m_drone_class = flight_drone.drone_class()
        m_drone_class.open(settings, index, cf, uri, g_args.no_route, g_args.no_led)

        try:
            g_mutex.acquire()
            g_drone_entity[uri] = m_drone_class
            g_drone_count += 1
            if g_drone_count >= len(g_settings["drones"]):
                g_begin_flight = True
        finally:
            g_mutex.release()

        try:
            # WAIT FOR DRONES TO GET READY
            while not g_begin_flight:
                time.sleep(.1)

            while not g_end_flight:
                m_drone_class.tick()
                time.sleep(.1)
        finally:
            m_drone_class.close()

    except:
        traceback.print_exc()

"""
def drone_thread(index):
    try:
        uri_list = list()
        for k, v in g_settings["drones"].items():
            uri_list.append(k)
        with SyncCrazyflie(uri_list, cf=Crazyflie(rw_cache='./cache')) as scf:
            reset_estimator(scf)
            drone_main(scf)
    except:
        traceback.print_exc()
"""

if __name__ == '__main__':
    try:
        try:
            args = parse_arguments()

            # Initialize the low-level drivers
            cflib.crtp.init_drivers()

            # This is used to let the kill thread work
            x = threading.Thread(target=thread_function)
            x.start()

            if g_settings["song"]:
                g_music_class.open(g_settings, args.no_music)
            g_unity_class.open(g_settings, args.no_unity)

            # This is used to let manage music and unity
            x = threading.Thread(target=thread_function2, args=(g_settings["flight_time"],))
            x.start()

            # Process the swarm
            factory = CachedCfFactory(rw_cache='./cache')
            uri_list = list()
            for k, v in g_settings["drones"].items():
                uri_list.append(k)
            with Swarm(uri_list, factory=factory) as swarm:
                swarm.parallel(reset_estimator)
                swarm.parallel(drone_main)

            """
            for index in range(0, len(g_settings["uri"])):
                x = threading.Thread(target=drone_thread, args=(index, ))
                x.start()
            """

            while not g_end_flight:
                time.sleep(1)
        finally:
            time.sleep(5)
            g_end_flight = True
    except:
        traceback.print_exc()

    os._exit(0)
