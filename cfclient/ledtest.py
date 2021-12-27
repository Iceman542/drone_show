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

#URI = uri_helper.uri_from_env(default='radio://0/60/2M/E6E6E6E6E6')
URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        cf = scf.cf

        # Set fade to color effect
        cf.param.set_value('ring.effect', '14')
        # Set fade time i seconds
        cf.param.set_value('ring.fadeTime', '5.0')
        # Set the RGB values in one uint32 0xRRGGBB
        cf.param.set_value('ring.fadeColor', '0x0000A0')
        time.sleep(1)
        cf.param.set_value('ring.fadeColor', '0x00A000')
        time.sleep(1)
        cf.param.set_value('ring.fadeColor', '0xA00000')
        time.sleep(1)
        time.sleep(0xffff)



        # Set solid color effect
        cf.param.set_value('ring.effect', '13')
        # Set the RGB values
        cf.param.set_value('ring.solidRed', '0')
        cf.param.set_value('ring.solidGreen', '100')
        cf.param.set_value('ring.solidBlue', '0')
        time.sleep(0xffff)

        # Set solid color effect
        cf.param.set_value('ring.effect', '7')
        # Set the RGB values
        cf.param.set_value('ring.solidRed', '100')
        cf.param.set_value('ring.solidGreen', '0')
        cf.param.set_value('ring.solidBlue', '0')
        time.sleep(0xffff)





        # Set virtual mem effect effect
        cf.param.set_value('ring.effect', '2')
        cf.param.set_value('ring.headlightEnable', '1')

        # Get LED memory and write to it
        mem = cf.mem.get_mems(MemoryElement.TYPE_DRIVER_LED)
        if len(mem) > 0:

            mem[0].leds[0].set(r=0,   g=100, b=0)
            mem[0].leds[3].set(r=0,   g=0,   b=100)
            mem[0].leds[6].set(r=100, g=0,   b=0)
            mem[0].leds[9].set(r=100, g=100, b=100)
            mem[0].write_data(None)
        else:
            print("No LED")

        time.sleep(2)






        # Set virtual mem effect effect
        cf.param.set_value('ring.effect', '13')

        # Get LED memory and write to it
        mem = cf.mem.get_mems(MemoryElement.TYPE_DRIVER_LED)
        if len(mem) > 0:
            mem[0].leds[0].set(r=0,   g=100, b=0)
            mem[0].leds[3].set(r=0,   g=0,   b=100)
            mem[0].leds[6].set(r=100, g=0,   b=0)
            mem[0].leds[9].set(r=100, g=100, b=100)
            mem[0].write_data(None)
        else:
            print("No LED")


        time.sleep(2)












"""
Ledring12Effect effectsFct[] =
{
  blackEffect,
  whiteSpinEffect,
  colorSpinEffect,
  tiltEffect,
  brightnessEffect,
  spinEffect2,
  doubleSpinEffect,
  solidColorEffect,
  ledTestEffect,
  batteryChargeEffect,
  boatEffect,
  siren,
  gravityLight,
  virtualMemEffect,
  fadeColorEffect,
  rssiEffect,
  locSrvStatus,
  timeMemEffect,
  lighthouseEffect,
};
"""