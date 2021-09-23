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
from cflib.crazyflie.log import LogConfig
from pynput.keyboard import Key, Controller
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

# Change uris according to your setup
URI0 = 'radio://0/80/2M/E7E7E7E7E5'
#URI1 = 'radio://0/80/2M/E7E7E7E7E7' # This is drone 2
# URI2 = 'radio://0/60/2M/E7E7E7E7E7'
# URI3 = 'radio://0/5/2M/E7E7E7E702'
# URI4 = 'radio://0/110/2M/E7E7E7E703'

# d: diameter of circle
# z: altitude
params0 = {'d': 1.0, 'z': 0.3}
#params1 = {'d': 1.0, 'z': 0.3}
# params2 = {'d': 0.0, 'z': 0.5}
# params3 = {'d': 1.0, 'z': 0.3}
# params4 = {'d': 1.0, 'z': 0.3}

uris = {
    URI0,
    #URI1,
    # URI2,
    # URI3,
    # URI4,
}

params = {
    URI0: [params0],
    #URI1: [params1],
    # URI2: [params2],
    # URI3: [params3],
    # URI4: [params4],
}

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

_continue = True

class EStop(Exception):
    pass

# This is a kill thread, by pressing enter
def thread_function():
    global _continue
    _continue = True
    x = input()
    _continue = False
    print("End of FLight")

def reset_estimator(scf):
    cf = scf.cf
    cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    cf.param.set_value('kalman.resetEstimation', '0')
    time.sleep(1)


def take_off(cf, z, in_time):
    take_off_time = in_time
    sleep_time = 0.1
    steps = int(take_off_time / sleep_time)
    vz = z / take_off_time

    for i in range(steps):
                                            #   vx, vy, yaw_rate, Z
        cf.commander.send_velocity_world_setpoint(0, 0, 0, vz)
        time.sleep(sleep_time)


def hover(scf, z, seconds):
    cf = scf.cf
    sleep_time = 0.1
    steps = int(seconds/sleep_time)

    # Hover in place
    for _ in range(steps):
        cf.commander.send_hover_setpoint(0, 0, 0, z)
        time.sleep(0.1)
        if e_stop_check() is False:
            return


def move(scf, seconds, vx, vy, yaw_rate, z):
    cf = scf.cf
    sleep_time = 0.1
    steps = int(seconds / sleep_time)

    for _ in range(steps):
        cf.commander.send_hover_setpoint(vx, vy, yaw_rate, z)
        time.sleep(0.1)
        if e_stop_check() is False:
            return


def land(cf, z, in_time):
    landing_time = in_time
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


def e_stop_check():
    if not _continue:
        raise EStop


# This function is taking the log and printing it
def log_stab_callback(timestamp, data, logconf):
    global _continue
    print('[%d][%s]: %s' % (timestamp, logconf.name, data))
    if "pm.state" in data:
        if data["pm.state"] == 3:  # State 3 is low power
             _continue = False

def run_sequence(scf, params):
    cf = scf.cf

    # Logging
    logconf = lg_stab
    cf.log.add_config(logconf)
    logconf.data_received_cb.add_callback(log_stab_callback)
    logconf.start()

    print("Beginning Flight")
    height = 1  # in meters

    e_stop_check()

    try:
        print("Take off")
        take_off(cf, height, 0.6)  # Time in seconds
        print("Hover")
        hover(scf, height, 5)
        print("Moving Foward")
        move(scf, 3, 0.35, 0, 0, height)  # (scf ,seconds, vx, vy, yaw_rate, z)
        print("Land")
        land(cf, height, 2)

    except EStop:
        print("E-Stop Triggered")
        land(cf, height, 2)
        logconf.stop()

    except Exception as e:
        print(e)



if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    # This is used to let the kill thread work
    x = threading.Thread(target=thread_function)
    x.start()

    # Logging attributes
    lg_stab = LogConfig(name='Stabilizer', period_in_ms=1000)
    lg_stab.add_variable('pm.batteryLevel', 'float')
    lg_stab.add_variable('pm.state', 'int8_t')
    lg_stab.add_variable('pm.vbat', 'float')

    factory = CachedCfFactory(rw_cache='./cache')
    with Swarm(uris, factory=factory) as swarm:
        swarm.parallel(reset_estimator)
        swarm.parallel(run_sequence, args_dict=params)

