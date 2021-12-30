#!/usr/bin/python3

# //  ***************************************************************************
# /// @file         flight_base.py
# /// @brief        This module will manage the base logic
# //  ***************************************************************************

g_begin_flight = False
g_end_flight = False
g_drone_entity = dict()

from abc import ABC, abstractmethod

class base_class:

    @abstractmethod
    def open(self, settings):
        pass

    @abstractmethod
    def tick(self):
        pass

    @abstractmethod
    def close(self):
        pass

# // ////////////////////////////////////////////////////////////////////////////
# // END flight_base.py
# // ////////////////////////////////////////////////////////////////////////////
