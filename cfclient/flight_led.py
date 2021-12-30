#!/usr/bin/python3

# //  ***************************************************************************
# /// @file         flight_led.py
# /// @brief        This module will manage the led logic
# ///     0: "Off",
# ///     1: "White spinner",
# ///     2: "Color spinner",
# ///     3: "Tilt effect",
# ///     4: "Brightness effect",
# ///     5: "Color spinner 2",
# ///     6: "Double spinner",
# ///     7: "Solid color effect",
# ///     8: "Factory test",
# ///     9: "Battery status",
# ///     10: "Boat lights",
# ///     11: "Alert",
# ///     12: "Gravity",
# ///     13: "LED tab",
# ///     14: "Color fader",
# ///     15: "Link quality",
# ///     16: "Location server status",
# ///     17: "Sequencer",
# ///     18: "Lighthouse quality",
# //  ***************************************************************************

import os
import time
import traceback

from flight_base import base_class

class led_class(base_class):
    def __init__(self):
        self.m_lights_timeout = float(0)
        self.m_lights_index = 0
        self.m_lights = None
        self.m_running = False

    def open(self, settings, cf, index):
        # SETUP LIGHTS
        self.m_drone_index = settings["index"]
        self.m_cf = cf
        self.m_lights = settings["led"][index]

        # TURN LIGHTS OFF
        if self.m_cf is not None:
            # Set default solid color effect
            self.m_cf.param.set_value('ring.effect', '0')

        self.m_running = True

    def tick(self):
        # Lights - (time, (r,g,b))
        try:
            if self.m_lights_timeout <= 0.0:
                self.m_lights_timeout = float(self.m_lights[self.m_lights_index][0])

                rgb = self.m_lights[self.m_lights_index][1]

                # Set the RGB values
                if self.m_cf is not None:
                    # lights = (bulb_index,r,g,b,visible)
                    self.m_cf.param.set_value('ring.effect', '7')
                    self.m_cf.param.set_value('ring.solidRed', str(rgb[0]))
                    self.m_cf.param.set_value('ring.solidGreen', str(rgb[1]))
                    self.m_cf.param.set_value('ring.solidBlue', str(rgb[2]))

                    # ????????
                    # g_drone_comms.send_lights(self.m_index, rgb)

                    self.m_lights_index += 1
            self.m_lights_timeout -= 0.1
        except:
            self.close()
        return self.m_running

    def close(self):
        # TURN LIGHTS OFF
        if self.m_cf is not None:
            # Set default solid color effect
            self.m_cf.param.set_value('ring.effect', '0')
            self.m_cf = None
        self.m_running = False

# *******************************
# TEST CODE
# *******************************
if __name__ == '__main__':
    try:
        import cflib.crtp
        from cflib.crazyflie import Crazyflie
        from cflib.crazyflie.mem import MemoryElement
        from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
        from cflib.utils import uri_helper

        from leds import led_1                        # <- CHANGE THIS
        led_test = led_1.LED_1

        # URI_drone = 'radio://0/60/2M/E6E6E6E6E6'    # <- CHANGE THIS
        URI_drone = 'radio://0/80/2M/E7E7E7E7E5'

        g_settings = {
            "drone": [URI_drone],
            "led": [led_test],
        }

        index = 0
        URI = uri_helper.uri_from_env(default=g_settings["drone"][g_settings["index"]])
        cflib.crtp.init_drivers()
        with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
            led = led_class()
            led.open(g_settings, scf.cf, index)
            while True:
                if not led.tick():
                    break
                time.sleep(0.1)

    except:
        traceback.print_exc()
    os._exit(0)

# // ////////////////////////////////////////////////////////////////////////////
# // END flight_led.py
# // ////////////////////////////////////////////////////////////////////////////