#!/usr/bin/env python
# -*- coding: utf-8 -*-

# vi: set autoindent noexpandtab tabstop=4 shiftwidth=4
import re

from configparser import ConfigParser

from plenticoreDataService import get_data
from plenticoreSessionService import get_session_key

import requests

from dbus_inverter import DbusInverter

from dbus.mainloop.glib import DBusGMainLoop

from gi.repository import GLib

import sys
import threading
import time


class DevState:
    WaitForDevice = 0
    Connect = 1
    Connected = 2


class DevStatistics:
    connection_ok = 0
    connection_ko = 0
    parse_error = 0
    last_connection_errors = 0  # reset every ok read
    last_time = 0
    reconnect = 0


class Kostal:
    ip = ''
    password = ''
    stats = DevStatistics
    interval = 10
    version = 1
    instance = 50
    max_retries = 10
    inverter_name = 'NO_NAME_PROVIDED'
    session_id = 'XXX'
    sw_version = ''
    position = 0
    dev_state = DevState.WaitForDevice
    dbus_inverter = []

    def __init__(self, name, ip, instance, password, interval, position):
        self.inverter_name = name
        self.ip = ip
        self.instance = instance
        self.password = password
        self.interval = interval
        self.position = position


global inverter

base_path = '/api/v1'


def push_statistics():
    global inverter
    inverter.dbus_inverter.set('/stats/connection_ok', inverter.stats.connection_ok)
    inverter.dbus_inverter.set('/stats/connection_error', inverter.stats.connection_ko)
    inverter.dbus_inverter.set('/stats/last_connection_errors', inverter.stats.last_connection_errors)
    inverter.dbus_inverter.set('/stats/parse_error', inverter.stats.parse_error)
    inverter.dbus_inverter.set('/stats/reconnect', inverter.stats.reconnect)


def parse_config():
    global inverter
    parser = ConfigParser()
    cfgname = 'kostal.ini'
    if len(sys.argv) > 1:
        cfgname = str(sys.argv[1])
    print('Parsing config: ' + cfgname)
    parser.read(cfgname)

    if len(parser.sections()) == 0:
        print("config seems to be empty...")
        exit(1)

    def get_password(section):
        if parser.has_option(section, 'password'):
            return parser.get(section, 'password')
        else:
            print('config section ' + section + ' is missing the password.')
            exit(1)

    def get_ip(section):
        if parser.has_option(section, 'ip'):
            ip = parser.get(section, 'ip')
            match = re.match(r"http:\/\/[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", ip)
            if match is None or match.span() != (0, len(ip)):
                print("Error: ip should be of format: 'http://123.123.123.123', instead got '" + ip + "'")
                exit(1)
            return ip + base_path
        else:
            print('config section ' + section + ' is missing the ip..')
            exit(1)

    def get_interval(section):
        if parser.has_option(section, 'interval'):
            return int(parser.get(section, 'interval'))
        else:
            print('config section ' + section + ' is missing the interval..')
            exit(1)

    def get_instance(section):
        if parser.has_option(section, 'instance'):
            return int(parser.get(section, 'instance'))
        else:
            print('config section ' + section + ' is missing the instance, using default 50...')
            return 50

    def get_position(section):
        if parser.has_option(section, 'position'):
            return int(parser.get(section, 'position'))
        else:
            print('config section ' + section + ' is missing the position, using default 0...')
            return 0

    section = parser.sections()[0]

    inverter = Kostal(section, get_ip(section), get_instance(section), get_password(section), get_interval(section),
                      get_position(section))

    print('Found config: ' + section)

    print(inverter.inverter_name, ' at ', inverter.ip)


def set_dbus_data(data):
    global inverter
    time_ms = int(round(time.time() * 1000))
    if inverter.stats.last_time == time_ms:
        inverter.dbus_inverter.inc('/stats/repeated_values')
        inverter.dbus_inverter.inc('/stats/last_repeated_values')
        print('got repeated value')
    else:
        inverter.stats.last_time = time_ms
        inverter.dbus_inverter.set('/stats/last_repeated_values', 0)

        inverter.dbus_inverter.set('/Ac/Power', (data['PT']))
        inverter.dbus_inverter.set('/Ac/Current', (data['IN0']), 1)
        inverter.dbus_inverter.set('/Ac/L1/Current', (data['IA']), 1)
        inverter.dbus_inverter.set('/Ac/L1/Voltage', (data['VA']))
        inverter.dbus_inverter.set('/Ac/L1/Power', (data['PA']))
        inverter.dbus_inverter.set('/Ac/L2/Current', (data['IB']), 1)
        inverter.dbus_inverter.set('/Ac/L2/Voltage', (data['VB']))
        inverter.dbus_inverter.set('/Ac/L2/Power', (data['PB']))
        inverter.dbus_inverter.set('/Ac/L3/Current', (data['IC']), 1)
        inverter.dbus_inverter.set('/Ac/L3/Voltage', (data['VC']))
        inverter.dbus_inverter.set('/Ac/L3/Power', (data['PC']))

        inverter.dbus_inverter.set('/Ac/Energy/Forward', (data['EFAT']))

        print("++++++++++")
        print("POWER Phase A: " + str(data['PA']) + "W")
        print("POWER Phase B: " + str(data['PB']) + "W")
        print("POWER Phase C: " + str(data['PC']) + "W")
        print("POWER Total: " + str(data['PT']) + "W")


def init_session():
    global inverter
    session_id, sw_version, api_version = get_session_key(inverter.password, inverter.ip)
    inverter.sw_version = sw_version
    inverter.session_id = session_id
    inverter.dev_state = DevState.Connected


def init_dbus():
    global inverter
    inverter.dbus_inverter = DbusInverter(inverter.inverter_name, inverter.ip, inverter.instance,
                                          '0',
                                          inverter.inverter_name,
                                          inverter.sw_version, '0.1', inverter.position)
    return


def read_data():
    global inverter
    try:
        print('reading data from ',
              inverter.inverter_name + ' inverter at ' + inverter.ip + ' using sessionid ' + inverter.session_id)
        data = get_data(inverter.ip, inverter.session_id)
        set_dbus_data(data)
        print('done.')
        return
    except (requests.exceptions.HTTPError, requests.exceptions.RequestException):
        print('Error reading from ' + inverter.ip)
        inverter.stats.connection_ko += 1
        inverter.stats.last_connection_errors += 1
        return 1


def cyclic_update(run_event):
    global inverter

    while run_event.is_set():
        print("Thread: doing")

        push_statistics()

        if inverter.stats.last_connection_errors > inverter.max_retries:
            print('Lost connection to kostal, reset')
            inverter.dev_state = DevState.Connect
            inverter.stats.last_connection_errors = 0
            inverter.stats.reconnect += 1
            inverter.dbus_inverter.set('/Connected', 0)
            inverter.dbus_inverter.set('/Ac/L1/Current', None)
            inverter.dbus_inverter.set('/Ac/L2/Current', None)
            inverter.dbus_inverter.set('/Ac/L3/Current', None)
            inverter.dbus_inverter.set('/Ac/L1/Power', None)
            inverter.dbus_inverter.set('/Ac/L2/Power', None)
            inverter.dbus_inverter.set('/Ac/L3/Power', None)
            inverter.dbus_inverter.set('/Ac/L1/Voltage', None)
            inverter.dbus_inverter.set('/Ac/L2/Voltage', None)
            inverter.dbus_inverter.set('/Ac/L3/Voltage', None)
            inverter.dbus_inverter.set('/Ac/Power', None)
            inverter.dbus_inverter.set('/Ac/Current', None)
            inverter.dbus_inverter.set('/Ac/Voltage', None)

        elif inverter.dev_state == DevState.Connected:
            read_data()
        else:
            print('invalid state...')

        time.sleep(inverter.interval)
    return


DBusGMainLoop(set_as_default=True)
parse_config()
init_session()
init_dbus()

try:
    run_event = threading.Event()
    run_event.set()

    update_thread = threading.Thread(target=cyclic_update, args=(run_event,))
    update_thread.start()

    mainloop = GLib.MainLoop()
    mainloop.run()

except (KeyboardInterrupt, SystemExit):
    mainloop.quit()
    run_event.clear()
    update_thread.join()
    print("Host: KeyboardInterrupt")
