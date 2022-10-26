#!/usr/bin/env python2

try:
    import gobject
    from gobject import idle_add
except:
    from gi.repository import GObject as gobject
    from gi.repository.GObject import idle_add
import os
import sys

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))

from vedbus import VeDbusService


class DbusInverter:
    dbusservice = []

    def __init__(self, dev, connection, device_instance, serial, product_name, firmware_version, process_version):

        print(__file__ + " starting up, connecting as pvinverter '" + dev + "' to dbus..")

        # Put ourselves on to the dbus
        dbus_name = 'com.victronenergy.pvinverter.' + dev
        print('dbus_name: ' + dbus_name)
        self.dbusservice = VeDbusService(dbus_name)

        # Add objects required by ve-api
        self.dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self.dbusservice.add_path('/Mgmt/ProcessVersion', process_version)
        self.dbusservice.add_path('/Mgmt/Connection', connection)  # todo
        self.dbusservice.add_path('/DeviceInstance', device_instance)
        self.dbusservice.add_path('/ProductId', 0xFFFF)  # 0xB012 ?
        self.dbusservice.add_path('/ProductName', product_name)
        self.dbusservice.add_path('/FirmwareVersion', firmware_version)
        self.dbusservice.add_path('/Serial', serial)
        self.dbusservice.add_path('/Connected', 1, writeable=True)
        self.dbusservice.add_path('/ErrorCode', '(0) No Error')
        self.dbusservice.add_path('/Position', 0)

        _kwh = lambda p, v: (str(v) + 'KWh')
        _a = lambda p, v: (str(v) + 'A')
        _w = lambda p, v: (str(v) + 'W')
        _v = lambda p, v: (str(v) + 'V')
        _s = lambda p, v: (str(v) + 's')
        _x = lambda p, v: (str(v))

        self.dbusservice.add_path('/Ac/Energy/Forward', None, gettextcallback=_kwh)
        self.dbusservice.add_path('/Ac/L1/Current', None, gettextcallback=_a)
        self.dbusservice.add_path('/Ac/L1/Energy/Forward', None, gettextcallback=_kwh)
        self.dbusservice.add_path('/Ac/L1/Power', None, gettextcallback=_w)
        self.dbusservice.add_path('/Ac/L1/Voltage', None, gettextcallback=_v)
        self.dbusservice.add_path('/Ac/L2/Current', None, gettextcallback=_a)
        self.dbusservice.add_path('/Ac/L2/Energy/Forward', None, gettextcallback=_kwh)
        self.dbusservice.add_path('/Ac/L2/Power', None, gettextcallback=_w)
        self.dbusservice.add_path('/Ac/L2/Voltage', None, gettextcallback=_v)
        self.dbusservice.add_path('/Ac/L3/Current', None, gettextcallback=_a)
        self.dbusservice.add_path('/Ac/L3/Energy/Forward', None, gettextcallback=_kwh)
        self.dbusservice.add_path('/Ac/L3/Power', None, gettextcallback=_w)
        self.dbusservice.add_path('/Ac/L3/Voltage', None, gettextcallback=_v)
        self.dbusservice.add_path('/Ac/Power', None, gettextcallback=_w)
        self.dbusservice.add_path('/Ac/Current', None, gettextcallback=_a)
        self.dbusservice.add_path('/Ac/Voltage', None, gettextcallback=_v)

        self.dbusservice.add_path('/stats/connection_ok', 0, gettextcallback=_x, writeable=True)
        self.dbusservice.add_path('/stats/connection_error', 0, gettextcallback=_x, writeable=True)
        self.dbusservice.add_path('/stats/parse_error', 0, gettextcallback=_x, writeable=True)
        self.dbusservice.add_path('/stats/repeated_values', 0, gettextcallback=_x, writeable=True)
        self.dbusservice.add_path('/stats/last_connection_errors', 0, gettextcallback=_x, writeable=True)
        self.dbusservice.add_path('/stats/last_repeated_values', 0, gettextcallback=_x, writeable=True)
        self.dbusservice.add_path('/stats/reconnect', 0, gettextcallback=_x)
        self.dbusservice.add_path('/Mgmt/intervall', 1, gettextcallback=_s, writeable=True)

    def invalidate(self):
        self.set('/Ac/L1/Power', [])
        self.set('/Ac/L2/Power', [])
        self.set('/Ac/L3/Power', [])
        self.set('/Ac/Power', [])

    def set(self, name, value, round_digits=0):
        if isinstance(value, float):
            self.dbusservice[name] = round(value, round_digits)
        else:
            self.dbusservice[name] = value

    def get(self, name):
        v = self.dbusservice[name]
        return v

    def inc(self, name):
        self.dbusservice[name] += 1
