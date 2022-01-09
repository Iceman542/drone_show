#!/usr/bin/python3

# //  ***************************************************************************
# /// @file         flight_music.py
# /// @brief        This module will manage the music logic
# //  ***************************************************************************

import os
import vlc
import time
import traceback

from flight_base import base_class

class music_class(base_class):
    m_running = False

    def __init__(self):
        self.m_song = None
        self.m_running = False

    def open(self, settings):
        self.m_song = vlc.MediaPlayer(settings["song"])

    def tick(self):
        try:
            if self.m_song and not self.m_running:
                self.m_song.play()
                self.m_running = True
        except:
            traceback.print_exc()
        return self.m_running

    def close(self):
        if self.m_running:
            self.m_song.stop()
            self.m_running = False

g_music_class = music_class()

# *******************************
# TEST CODE
# *******************************
if __name__ == '__main__':
    try:
        try:
            from uri_local import g_settings

            g_music_class.open(g_settings)
            g_music_class.tick()
            time.sleep(10)
        finally:
            g_music_class.close()
    except:
        traceback.print_exc()
    os._exit(0)

# // ////////////////////////////////////////////////////////////////////////////
# // END flight_music.py
# // ////////////////////////////////////////////////////////////////////////////
