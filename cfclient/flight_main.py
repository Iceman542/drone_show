import os
import logging
import time
import threading
import traceback

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

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

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

def find_drone_index(uri):
    for i in range(0, len(g_settings["uri"])):
        if g_settings["uri"][i] == uri:
            return i
    return None

def reset_estimator(scf):
    try:
        cf = scf.cf
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
    index = 0
    global g_begin_flight
    global g_drone_entity
    global g_drone_count

    try:
        uri = g_settings["uri"][index]
        cf = scf.cf

        m_drone_class = flight_drone.drone_class()
        m_drone_class.open(g_settings, index, cf, uri)

        try:
            g_mutex.acquire()
            g_drone_entity[uri] = m_drone_class
            g_drone_count += 1
            if g_drone_count >= len(g_settings["uri"]):
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

def drone_thread(index):
    try:
        with SyncCrazyflie(g_settings["uri"][index], cf=Crazyflie(rw_cache='./cache')) as scf:
            reset_estimator(scf)
            drone_main(scf, index)
    except:
        traceback.print_exc()

if __name__ == '__main__':
    try:
        try:
            # Initialize the low-level drivers
            cflib.crtp.init_drivers()

            # This is used to let the kill thread work
            x = threading.Thread(target=thread_function)
            x.start()

            if g_settings["song"]:
                g_music_class.open(g_settings)
            g_unity_class.open(g_settings)

            # This is used to let manage music and unity
            x = threading.Thread(target=thread_function2, args=(g_settings["flight_time"],))
            x.start()

            # Process the swarm
            factory = CachedCfFactory(rw_cache='./cache')
            with Swarm(g_settings["uri"], factory=factory) as swarm:
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
