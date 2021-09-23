"""
Simple example that connects to the crazyflie at `URI` and writes to
the LED memory so that individual leds in the LED-ring can be set,
it has been tested with (and designed for) the LED-ring deck.
Change the URI variable to your Crazyflie configuration.
"""
import logging
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie

from cflib.crazyflie.mem import MemoryElement
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

#URI = uri_helper.uri_from_env(default='usb://0')
URI = uri_helper.uri_from_env(default='radio://0/60/2M/E6E6E6E6E6')

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)


if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        cf = scf.cf

        # Set virtual mem effect effect
        cf.param.set_value('ring.effect', '13')

        # Get LED memory and write to it
        mem = cf.mem.get_mems(MemoryElement.TYPE_DRIVER_LED)
        if len(mem) > 0:
            mem[0].leds[0].set(r=0,   g=100, b=0)
            mem[0].leds[1].set(r=0,   g=200, b=0)
            mem[0].leds[3].set(r=0,   g=0,   b=100)
            mem[0].leds[4].set(r=0,   g=0,   b=200)
            mem[0].leds[6].set(r=100, g=0,   b=0)
            mem[0].leds[6].set(r=200, g=0,   b=0)
            mem[0].leds[9].set(r=100, g=100, b=100)
            mem[0].write_data(None)

        time.sleep(2)

