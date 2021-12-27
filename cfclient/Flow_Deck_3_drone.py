
"""
Simple example that connects to the crazyflie at `URI` and runs a figure 8
sequence. This script requires some kind of location system, it has been
tested with (and designed for) the flow deck.
Change the URI variable to your Crazyflie configuration.
"""
import os
import sys
import logging
import time
import threading
import traceback

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.swarm import CachedCfFactory, Swarm
from pynput.keyboard import Key, Controller
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

import Flow_Manager
from uri_local import g_routes, g_uris, g_unity

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

# This is a kill thread, by pressing enter
def thread_function():
    Flow_Manager.begin_flight(len(g_routes))
    x = input()
    Flow_Manager.end_flight()

def reset_estimator(scf):
    print("Pre-Flight Check")
    cf = scf.cf
    cf.param.set_value('kalman.initialX', 0)
    cf.param.set_value('kalman.initialY', 0)
    cf.param.set_value('kalman.initialZ', 0)

    cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    cf.param.set_value('kalman.resetEstimation', '0')
    time.sleep(2)

# This function is taking the log and printing it
def log_stab_callback(timestamp, data, logconf):
    uri = logconf.cf.link_uri
    #print('[%d][%s]: %s' % (timestamp, logconf.name, data))
    Flow_Manager.update_callback(uri, data)

def run_sequence(scf):
    global g_routes

    # Flight Controller
    try:
        uri = scf.cf.link_uri
        fm = Flow_Manager.FlowManagerClass(scf, uri)
        fm.run_sequence(fm, g_routes[uri])
        #CHECK PLEASE, IS FM THE CORRECT PASS? Run sequence expects self
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

            # Expand the routes from seconds to 0.1 second intervals
            g_routes = Flow_Manager.expand_routes(g_routes)

            # Connect to unity
            Flow_Manager.g_drone_comms = Flow_Manager.FlowManagerCommunications()
            Flow_Manager.g_drone_comms.open(g_unity)

            # Process the swarm
            factory = CachedCfFactory(rw_cache='./cache')
            with Swarm(g_uris, factory=factory) as swarm:
                swarm.parallel(reset_estimator)
                swarm.parallel(run_sequence)
        finally:
            Flow_Manager.g_drone_comms.close()
    except:
        traceback.print_exc()

    os._exit(0)
