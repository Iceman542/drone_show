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
from pynput.keyboard import Key, Controller
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

height = 0

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
    print("Height: ", height)
    land(cf, height)
    scf._continue = False
    print("Kill Confirmed")


def reset_estimator(scf):
    print("Pre-Flight Check")
    cf = scf.cf
    cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    cf.param.set_value('kalman.resetEstimation', '0')
    time.sleep(2)


def take_off(cf, z):
    take_off_time = .5
    sleep_time = 0.1
    steps = int(take_off_time / sleep_time)
    vz = z / take_off_time

    for i in range(steps):
                                            #   vx, vy, yaw_rate, Z
        cf.commander.send_velocity_world_setpoint(0, 0, 0, vz)
        time.sleep(sleep_time)


def hover(scf, z, seconds):
    cf = scf.cf

    # Hover in place
    for _ in range(seconds):
        cf.commander.send_hover_setpoint(0, 0, 0, z)
        time.sleep(0.1)
        if e_stop_check(scf, z):
            return


def land(cf, z):
    landing_time = 1.0
    sleep_time = 0.1
    steps = int(landing_time / sleep_time)
    vz = -z / landing_time

    for _ in range(steps):
                                    #   vx, vy, yaw_rate, Z
        cf.commander.send_hover_setpoint(0, 0, 0, vz)
        time.sleep(sleep_time)

    cf.commander.send_stop_setpoint()
    # Make sure that the last packet leaves before the link is closed
    # since the message queue is not flushed before closing
    time.sleep(0.1)

    # kill thread
    keyboard = Controller()
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)


def e_stop_check(scf, z):
    if not scf._continue:
        land(z)
        return False


def run_sequence(scf, params):
    # This is used to let the kill thread work
    x = threading.Thread(target=thread_function, args=(scf,))
    x.start()

    cf = scf.cf

    print("Beginning Flight")
    global height
    height = 1  # in meters
    e_stop_check(scf, height)

    print("Take off")
    take_off(cf, height)
    print("Hover")
    hover(scf, height, 30)  # every 10 is 1 second

    # Checks if e stop was pressed
    if e_stop_check(scf, height):
        return
    print("Land")
    land(cf, height)

if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    factory = CachedCfFactory(rw_cache='./cache')
    with Swarm(uris, factory=factory) as swarm:
        swarm.parallel(reset_estimator)
        swarm.parallel(run_sequence, args_dict=params)
