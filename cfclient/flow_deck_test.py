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
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

#URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')
URI = uri_helper.uri_from_env(default='radio://0/60/2M/E6E6E6E6E6')
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

def start(scf):
    # This is used to let the kill thread work
    x = threading.Thread(target=thread_function, args=(scf,))
    x.start()

    cf = scf.cf

    print("Pre-Flight Check")
    cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    cf.param.set_value('kalman.resetEstimation', '0')
    time.sleep(2)

    print("Beginning Flight")
    if not scf._continue:
        return

    # Take off
    for y in range(10):
                                    #   yx, vy, yaw_rate, Z
        cf.commander.send_hover_setpoint(0, 0, 0, y / 25)
        time.sleep(0.1)
        if not scf._continue:
            return

    # _ means you don't care about the value just that it the loop happens that many times (Everything in meters)
    # Hover in place
    for _ in range(20):
        cf.commander.send_hover_setpoint(0, 0, 0, 0.8)
        time.sleep(0.1)
        if not scf._continue:
            return

    # move foward (x) at .1 yaw
    for _ in range(50):
        cf.commander.send_hover_setpoint(0.25, 0, .1, 0.8)
        time.sleep(0.1)
        if not scf._continue:
            return

    # Hover
    for _ in range(20):
        cf.commander.send_hover_setpoint(0, 0, 0, 0.8)
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

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        start(scf)
