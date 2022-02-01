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

    def open(self, settings, cf, no_led):
        if not no_led:
            # SETUP LIGHTS
            self.m_cf = cf
            self.m_lights = settings["led"]

            # TURN LIGHTS OFF
            if self.m_cf is not None:
                # Set default solid color effect
                self.m_cf.param.set_value('ring.effect', '0')
            self.m_running = True

    # off/solid/whitespinner/colorspinner/colorspinner2/doublespinner

    def tick(self):
        # Lights - (time, (r,g,b))
        try:
            if self.m_running:
                if self.m_lights_timeout <= 0.0:
                    ref = self.m_lights[self.m_lights_index]
                    rgb = ref[1]
                    self.m_lights_timeout = float(ref[0])

                    effect_name = "solid"
                    if len(ref) > 2:
                        effect_name = ref[2]

                    # Set the RGB values
                    if self.m_cf is not None:
                        if effect_name == "off":
                            effect = '0'
                        elif effect_name == "whitespinner":
                            effect = '1'
                        elif effect_name == "colorspinner":
                            effect = '2'
                        elif effect_name == "colorspinner2":
                            effect = '5'
                        elif effect_name == "doublespinner":
                            effect = '6'
                        elif effect_name == "ledtab":
                            effect = '13'
                        else:
                            effect = '7'

                        if effect == '13':
                            self.m_cf.param.set_value('ring.effect', '0')
                            time.sleep(0.1)
                            self.m_cf.param.set_value('ring.effect', effect)
                            mem = self.m_cf.mem.get_mems(MemoryElement.TYPE_DRIVER_LED)
                            if len(mem) > 0:
                                ledtabs = ref[3]
                                for l in ledtabs:
                                    index = l[0]
                                    r, g, b = l[1]
                                    mem[0].leds[l[0]].set(r=r, g=g, b=b)
                                mem[0].write_data(None)

                        else:
                            # lights = (bulb_index,r,g,b,visible)
                            self.m_cf.param.set_value('ring.effect', effect)
                            self.m_cf.param.set_value('ring.solidRed', str(rgb[0]))
                            self.m_cf.param.set_value('ring.solidGreen', str(rgb[1]))
                            self.m_cf.param.set_value('ring.solidBlue', str(rgb[2]))

                            # ????????
                            # g_drone_comms.send_lights(self.m_index, rgb)

                        self.m_lights_index += 1
                self.m_lights_timeout -= 0.1
        except:
            self.close()
            #traceback.print_exc()
        return self.m_running

    def close(self):
        # TURN LIGHTS OFF
        if self.m_cf is not None:
            # Set default solid color effect
            self.m_cf.param.set_value('ring.effect', '0')
            time.sleep(0.1)
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

        from leds import led_5                        # <- CHANGE THIS

        uri = 'radio://0/60/2M/E6E6E6E6E6'
        settings = {"index": 0, "led": led_5.LED_5}

        cflib.crtp.init_drivers()
        with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
            led = led_class()
            led.open(settings, scf.cf, False)
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
