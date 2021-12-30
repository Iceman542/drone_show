import os
import logging
import time
import threading
import traceback

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
#from cflib.crazyflie.swarm import CachedCfFactory, Swarm

from flight_base import g_begin_flight, g_end_flight, g_drone_entity
from flight_music import g_music_class
from flight_unity import g_unity_class
from uri_local import g_settings
import flight_drone

g_mutex = threading.Lock()

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

# This is a kill thread, by pressing ENTER
def thread_function():
    global g_end_flight

    input()                             # WAIT FOR ENTER
    print("ENTER pressed!!!")
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

def drone_main(index, settings):
    global g_begin_flight
    global g_drone_entity

    try:
        uri = g_settings["uri"][index]
        scf = SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache'))
        cf = scf.cf
        count = len(g_settings["uri"])

        m_drone_class = flight_drone.drone_class()
        m_drone_class.open(g_settings, index, cf, uri)

        try:
            g_mutex.acquire()
            g_drone_entity[uri] = m_drone_class
            if len(g_drone_entity) == count:
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

# ********************* #
# BEGIN - DEBUG SECTION #
g_debugging = True
if g_debugging:
    from uri_local import UNITY_SETTINGS, START_POS_0
    URI_drone = 'radio://0/80/2M/E7E7E7E7E7'
    ROUTE_0 = [
        (0, 0, 1, 1),       # go up
        (0, 0, 1, 2),       # hover
        (1, 0, 0.5, 2),     # go forward and down
        (0, 0, 0.5, 3),     # hover
        (0, 0.5, 1, 2),     # go left
        (0, -1, 1, 2),      # go right
        (0, 0, 1, 2),       # hover
        (1, 0, 1, 4),       # foward
        (0, -0.5, 1.5, 2),  # go right and up
        (-1, 0, 1.5, 3),    # Back and up
        (0.5, 0.5, 1.5, 2), # go left and foward
        (0, 0, 1, 2),       # back to takeoff spot
    ]
    LED_0 = [
        (4, (0, 0, 0)),
    ]
    g_settings = {
        "song": None, # "Crystallize_v1.mp3",
        "unity": UNITY_SETTINGS,
        "flight_time": 30,

        "uri": [URI_drone],
        "led": [LED_0],
        "route": [ROUTE_0],
        "start_pos": [START_POS_0]
    }
    g_debugging = True
# END - DEBUG SECTION #
# ******************* #

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
            """
            if not g_debugging:
                factory = CachedCfFactory(rw_cache='./cache')
                with Swarm(g_settings["uri"], factory=factory) as swarm:
                    swarm.parallel(drone_main)
            """

            for index in range(0, len(g_settings["uri"])):
                x = threading.Thread(target=drone_main, args=(index, g_settings, ))
                x.start()
            while not g_end_flight:
                time.sleep(1)
        finally:
            time.sleep(5)
            g_end_flight = True
    except:
        traceback.print_exc()

    os._exit(0)
