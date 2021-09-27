"""
Simple example that connects to the crazyflie at `URI` and runs a figure 8
sequence. This script requires some kind of location system, it has been
tested with (and designed for) the flow deck.
Change the URI variable to your Crazyflie configuration.
"""
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

# Change uris according to your setup
URI0 = 'radio://0/60/2M/E6E6E6E6E6'
#URI0 = 'radio://0/80/2M/E7E7E7E7E7'
#URI1 = 'radio://0/80/2M/E7E7E7E7E5' # This is drone 2
# URI2 = 'radio://0/60/2M/E7E7E7E7E7'
# URI3 = 'radio://0/5/2M/E7E7E7E702'
# URI4 = 'radio://0/110/2M/E7E7E7E703'

# (x_meters, y_meters, z_meters, rate-mps, time_seconds)
g_route0 = [
    (0, 0, 1, 1),       # go up
    (0, 0, 1, 2),       # hover
    (0.5, 0, 1, 2),     # go forward
    (-0.5, 0, 1, 2),    # go backwards
    (0, 0, 1, 2),       # hover
    (0, 0.5, 1, 2),     # go left
    (0, -0.5, 1, 2),    # go right
    (0, 0, 1, 2),       # hover
]

"""
g_route1 = [
    (0, 0, 1, 2),   # go up
    (1, 0, 1, 2),   # go right
    (1, 1, 1, 2),   # go forward
]
g_routes = [g_route0, g_route1]
"""
g_routes = [g_route0]

# d: diameter of circle
# z: altitude
params0 = {'d': 1.0, 'z': 0.3, 'route': 0}
#params1 = {'d': 1.0, 'z': 0.3, 'route': 1}
# params2 = {'d': 0.0, 'z': 0.5, 'route': 2}
# params3 = {'d': 1.0, 'z': 0.3, 'route': 3}
# params4 = {'d': 1.0, 'z': 0.3, 'route': 4}

uris = {
    URI0,
    # URI1,
    # URI2,
    # URI3,
    # URI4,
}

params = {
    URI0: [params0],
    # URI1: [params1],
    # URI2: [params2],
    # URI3: [params3],
    # URI4: [params4],
}

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

# This is a kill thread, by pressing enter
def thread_function():
    Flow_Manager.begin_flight(len(params))
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

def run_sequence(scf, params):
    global g_routes

    # Flight Controller
    try:
        fm = Flow_Manager.FlowManagerClass(scf, params, scf.cf.link_uri)
        fm.run_sequence(g_routes[params['route']])
    except:
        traceback.print_exc()

if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    # This is used to let the kill thread work
    x = threading.Thread(target=thread_function)
    x.start()

    # Expand the routes from seconds to 0.1 second intervals
    g_routes = Flow_Manager.expand_routes(g_routes)

    # Process the swarm
    factory = CachedCfFactory(rw_cache='./cache')
    with Swarm(uris, factory=factory) as swarm:
        swarm.parallel(reset_estimator)
        swarm.parallel(run_sequence, args_dict=params)
    sys.exit(0)
