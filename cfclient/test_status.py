import logging
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger

# URI to the Crazyflie to connect to

uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')
#uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')
#uri = uri_helper.uri_from_env(default='usb://0/E7E7E7E7E7')

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

def log_stab_callback(timestamp, data, logconf):
    print('[%d][%s]: %s' % (timestamp, logconf.name, data))

def simple_log_async(scf, logconf):
    cf = scf.cf
    cf.log.add_config(logconf)
    logconf.data_received_cb.add_callback(log_stab_callback)
    logconf.start()
    time.sleep(30)
    logconf.stop()

"""
de: Select all

{
            "acc": {
                "y": "LOG_OBJ",
                "x": "LOG_OBJ",
                "z": "LOG_OBJ",
                "zw": "LOG_OBJ",
                "mag2": "LOG_OBJ"
            },
            "mag": {
                "y": "LOG_OBJ",
                "x": "LOG_OBJ",
                "z": "LOG_OBJ"
            },
            "stabilizer": {
                "thrust": "LOG_OBJ",
                "yaw": "LOG_OBJ",
                "roll": "LOG_OBJ",
                "pitch": "LOG_OBJ"
            },
            "gyro": {
                "y": "LOG_OBJ",
                "x": "LOG_OBJ",
                "z": "LOG_OBJ"
            },
            "sys": {
                "canfly": "LOG_OBJ"
            },
            "radio": {
                "rssi": "LOG_OBJ"
            },
            "mag_raw": {
                "y": "LOG_OBJ",
                "x": "LOG_OBJ",
                "z": "LOG_OBJ"
            },
            "motor": {
                "m4": "LOG_OBJ",
                "m1": "LOG_OBJ",
                "m3": "LOG_OBJ",
                "m2": "LOG_OBJ"
            },
            "altHold": {
                "vSpeed": "LOG_OBJ",
                "target": "LOG_OBJ",
                "err": "LOG_OBJ",
                "vSpeedASL": "LOG_OBJ",
                "vSpeedAcc": "LOG_OBJ",
                "zSpeed": "LOG_OBJ"
            },
            "vpid": {
                "i": "LOG_OBJ",
                "p": "LOG_OBJ",
                "pid": "LOG_OBJ",
                "d": "LOG_OBJ"
            },
            "baro": {
                "aslRaw": "LOG_OBJ",
                "aslLong": "LOG_OBJ",
                "pressure": "LOG_OBJ",
                "temp": "LOG_OBJ",
                "asl": "LOG_OBJ"
            },
            "pm": {
                "state": "LOG_OBJ",
                "vbat": "LOG_OBJ",
                "chargeCurrent": "LOG_OBJ"
            }
        }
"""

if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    lg_stab = LogConfig(name='Stabilizer', period_in_ms=1000)
    """
    lg_stab.add_variable('stabilizer.roll', 'float')
    lg_stab.add_variable('stabilizer.pitch', 'float')
    lg_stab.add_variable('stabilizer.yaw', 'float')
    """

    """
    lg_stab.add_variable('gyro.x', 'float')
    lg_stab.add_variable('gyro.y', 'float')
    lg_stab.add_variable('gyro.z', 'float')
    """
    lg_stab.add_variable('pm.batteryLevel', 'float')
    lg_stab.add_variable('pm.state', 'int8_t')
    lg_stab.add_variable('pm.vbat', 'float')
    lg_stab.add_variable('pm.chargeCurrent', 'float')

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:

        simple_log_async(scf, lg_stab)
