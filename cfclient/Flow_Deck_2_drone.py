"""
Simple example that connects to the crazyflie at `URI` and runs a figure 8
sequence. This script requires some kind of location system, it has been
tested with (and designed for) the flow deck.
Change the URI variable to your Crazyflie configuration.
"""
import logging
import time
import threading

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.swarm import CachedCfFactory, Swarm
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

# Change uris according to your setup
URI0 = 'radio://0/80/2M/E7E7E7E7E7'
# URI1 = 'radio://0/60/2M/E7E7E7E7E5'
# URI2 = 'radio://0/60/2M/E7E7E7E7E7'
# URI3 = 'radio://0/5/2M/E7E7E7E702'
# URI4 = 'radio://0/110/2M/E7E7E7E703'

# d: diameter of circle
# z: altitude
params0 = {'d': 1.0, 'z': 0.3}
# params1 = {'d': 1.0, 'z': 0.3}
# params2 = {'d': 0.0, 'z': 0.5}
# params3 = {'d': 1.0, 'z': 0.3}
# params4 = {'d': 1.0, 'z': 0.3}

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
def thread_function(scf):
    scf._continue = True
    cf = scf.cf
    x = input()
    cf.commander.send_stop_setpoint()
    scf._continue = False
    print("Kill Confirmed")


def reset_estimator(scf):
    print("Pre-Flight Check")
    cf = scf.cf
    cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    cf.param.set_value('kalman.resetEstimation', '0')
    time.sleep(2)


def run_sequence(scf, params):
    # This is used to let the kill thread work
    x = threading.Thread(target=thread_function, args=(scf,))
    x.start()

    cf = scf.cf

    print("Beginning Flight")
    if not scf._continue:
        return

    # Take off low
    for y in range(10):
                                    #   vx, vy, yaw_rate, Z
        cf.commander.send_hover_setpoint(0, 0, 0, y / 25)
        time.sleep(0.1)
        if not scf._continue:
            return

    # _ means you don't care about the value just that it the loop happens that many times (Everything in meters)
    # Hover in place
    for _ in range(10):
        cf.commander.send_hover_setpoint(0, 0, 0, 1)
        time.sleep(0.1)
        if not scf._continue:
            return

    # Hover in place
    for _ in range(20):
        cf.commander.send_hover_setpoint(0, 0, 0, 1)
        time.sleep(0.1)
        if not scf._continue:
            return

    # move foward (x) at .1 yaw
    for _ in range(50):
        cf.commander.send_hover_setpoint(0.25, 0, .3, 1)
        time.sleep(0.1)
        if not scf._continue:
            return

    # Hover
    for _ in range(20):
        cf.commander.send_hover_setpoint(0, 0, 0, 1)
        time.sleep(0.1)
        if not scf._continue:
            return
    # Land
    for y in range(10):
        cf.commander.send_hover_setpoint(0, 0, 0, (10 - y) / 25)
        time.sleep(0.1)
        if not scf._continue:
            return

    cf.commander.send_stop_setpoint()

if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    factory = CachedCfFactory(rw_cache='./cache')
    with Swarm(uris, factory=factory) as swarm:
        swarm.parallel(reset_estimator)
        swarm.parallel(run_sequence, args_dict=params)
