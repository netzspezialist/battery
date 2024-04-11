#!/usr/bin/python3
import argparse
from datetime import datetime
import json
import logging
from optparse import Values
import sys
import asyncio
import time

import influxdb_client
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from daly_bms_bluetooth import DalyBMSBluetooth

class DalyBMSConnection():
    def __init__(self, mac_address,request_retries=3, logger=None):
        self.bt_bms = DalyBMSBluetooth(request_retries,logger)
        self.mac_address = mac_address
        self.connected = False

    async def connect(self):
        self.connected = await self.bt_bms.connect(mac_address=self.mac_address)

    async def update_cell_voltages(self):
        if not self.connected:
           await self.connect()
        return self.bt_bms.get_cell_voltages()


    async def get_cell_voltage_range(self):
        if not self.connected:
           await self.connect()
        return await self.bt_bms.get_cell_voltage_range()

    async def get_status(self):
        if not self.connected:
           await self.connect()
        return await self.bt_bms.get_status()

    async def get_temps2(self):
        if not self.connected:
           await self.connect()
        return await self.bt_bms.get_max_min_temperature()

    async def get_soc(self):
        if not self.connected:
           await self.connect()
        return await self.bt_bms.get_soc()

    async def get_mosfet(self):
        if not self.connected:
           await self.connect()
        return await self.bt_bms.get_mosfet_status()

    async def get_temps(self):
        if not self.connected:
           await self.connect()
        return await self.bt_bms.get_temperatures()

    async def get_bal(self):
        if not self.connected:
           await self.connect()
        return await self.bt_bms.get_balancing_status()

    async def get_errors(self):
        if not self.connected:
           await self.connect()
        return await self.bt_bms.get_errors()
    
    async def get_cell_voltages(self):
        if not self.connected:
            await self.connect()
        return await self.bt_bms.get_cell_voltages()

    async def get_all(self):
        if not self.connected:
           await self.connect()
        return await self.bt_bms.get_all()

    async def disconnect(self):
        if not self.connected:
           return
        return await self.bt_bms.disconnect()


parser = argparse.ArgumentParser()
parser.add_argument("-d", "--device",
                    help="MAC address, e.g. 88:99:AA:BB:CC",
                    type=str)
parser.add_argument("--status", help="show status", action="store_true")
parser.add_argument("--soc", help="show voltage, current, SOC", action="store_true")
parser.add_argument("--mosfet", help="show mosfet status", action="store_true")
parser.add_argument("--cell-voltages", help="show cell voltages", action="store_true")
parser.add_argument("--temperatures", help="show temperature sensor values", action="store_true")
parser.add_argument("--balancing", help="show cell balancing status", action="store_true")
parser.add_argument("--errors", help="show BMS errors", action="store_true")
parser.add_argument("--all", help="show all", action="store_true")
parser.add_argument("--cell-voltage-range", help="show cell voltage range", action="store_true")
parser.add_argument("--influx", help="write to influx", action="store_true")
parser.add_argument("--check", help="Nagios style check", action="store_true")
parser.add_argument("--set-discharge-mosfet", help="'on' or 'off'", type=str)
parser.add_argument("--retry", help="retry X times if the request fails, default 5", type=int, default=5)
parser.add_argument("--verbose", help="Verbose output", action="store_true")

parser.add_argument("--mqtt", help="Write output to MQTT", action="store_true")
parser.add_argument("--mqtt-hass", help="MQTT Home Assistant Mode", action="store_true")
parser.add_argument("--mqtt-topic",
                    help="MQTT topic to write to. default daly_bms",
                    type=str,
                    default="daly_bms")
parser.add_argument("--mqtt-broker",
                    help="MQTT broker (server). default localhost",
                    type=str,
                    default="localhost")
parser.add_argument("--mqtt-port",
                    help="MQTT port. default 1883",
                    type=int,
                    default=1883)
parser.add_argument("--mqtt-user",
                    help="Username to authenticate MQTT with",
                    type=str)
parser.add_argument("--mqtt-password",
                    help="Password to authenticate MQTT with",
                    type=str)
parser.add_argument("-C","--configfile",
                    nargs="?",
                    type=str,
                    help="Full location of config file (default None, /etc/dalybt.conf if -C supplied)",
                    const="/etc/dalybt.conf",
                    default=None,)
parser.add_argument("--daemon", action="store_true", help="Run as daemon",default=False)
parser.add_argument("--daemon-pause", type=int, help="Sleep time for daemon",default=60)
args = parser.parse_args()

log_format = '%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s'
if args.verbose:
    level = logging.DEBUG
else:
    level = logging.WARNING

logging.basicConfig(level=level, format=log_format, datefmt='%H:%M:%S')

logger = logging.getLogger()
#print (logger)

    # If config file specified, process
if args.configfile:
    import configparser
    logger.debug(f"args.configfile is true: {args.configfile}")
    config = configparser.ConfigParser()
    try:
        config.read(args.configfile)
    except configparser.DuplicateSectionError as e:
        logger.error(f"Config File '{args.configfile}' has duplicate sections")
        logger.error(e)
        exit(1)
    sections = config.sections()
    # Check setup section exists
    if "SETUP" not in config:
        logger.error(f"Config File '{args.configfile}' is missing the required 'SETUP' section")
        exit(1)
    # Process setup section
    args.daemon_pause = config["SETUP"].getint("daemon-pause", fallback=60)
    # Overide mqtt_broker settings
    args.mqtt =  config["SETUP"].getboolean("mqtt", fallback=args.mqtt)
    args.mqtt_hass = config["SETUP"].getboolean("mqtt-hass", fallback=args.mqtt_hass)
    args.mqtt_broker = config["SETUP"].get("mqtt-broker", fallback=args.mqtt_broker)
    args.mqtt_port = config["SETUP"].getint("mqtt-port", fallback=args.mqtt_port)
    args.mqtt_user = config["SETUP"].get("mqtt-user", fallback=args.mqtt_user)
    args.mqtt_password = config["SETUP"].get("mqtt-password", fallback=args.mqtt_password)
    sections.remove("SETUP")

    args.device = config["DALYBTBMS"].get("device", fallback=None)

#print(args)

bms = DalyBMSConnection(mac_address=args.device,request_retries=3, logger=logger )
#asyncio.run(bms.connect())

result = False
mqtt_client = None
if args.mqtt:
    import paho.mqtt.client as paho

    mqtt_client = paho.Client()
    mqtt_client.enable_logger(logger)
    mqtt_client.username_pw_set(args.mqtt_user, args.mqtt_password)
    mqtt_client.connect(args.mqtt_broker, port=args.mqtt_port)
    mqtt_client.loop_start()

def build_mqtt_hass_config_discovery(base):
    # Instead of daly_bms should be here added a proper name (unique), like serial or something
    # At this point it can be used only one daly_bms system with hass discovery

    hass_config_topic = f'homeassistant/sensor/daly_bms/{base.replace("/", "_")}/config'
    hass_config_data = {}

    hass_config_data["unique_id"] = f'daly_bms_{base.replace("/", "_")}'
    hass_config_data["name"] = f'Daly BMS {base.replace("/", " ")}'

    if 'soc_percent' in base:
        hass_config_data["device_class"] = 'battery'
        hass_config_data["unit_of_measurement"] = '%'
    elif 'voltage' in base:
        hass_config_data["device_class"] = 'voltage'
        hass_config_data["unit_of_measurement"] = 'V'
    elif 'current' in base:
        hass_config_data["device_class"] = 'current'
        hass_config_data["unit_of_measurement"] = 'A'
    elif 'temperatures' in base:
        hass_config_data["device_class"] = 'temperature'
        hass_config_data["unit_of_measurement"] = '°C'
    else:
        pass

    hass_config_data["json_attributes_topic"] = f'{args.mqtt_topic}{base}'
    hass_config_data["state_topic"] = f'{args.mqtt_topic}{base}'

    hass_device = {
        "identifiers": ['daly_bms'],
        "manufacturer": 'Daly',
        "model": 'Currently not available',
        "name": 'Daly BMS',
        "sw_version": 'Currently not available'
    }
    hass_config_data["device"] = hass_device

    return hass_config_topic, json.dumps(hass_config_data)


def mqtt_single_out(topic, data, retain=False):
    logger.debug(f'Send data: {data} on topic: {topic}, retain flag: {retain}')
    mqtt_client.publish(topic, data, retain=retain)

def mqtt_iterator(result, base=''):
    for key in result.keys():
        if type(result[key]) == dict:
            mqtt_iterator(result[key], f'{base}/{key}')
        else:
            if args.mqtt_hass:
                logger.debug('Sending out hass discovery message')
                topic, output = build_mqtt_hass_config_discovery(f'{base}/{key}')
                mqtt_single_out(topic, output, retain=True)

            if type(result[key]) == list:
                val = json.dumps(result[key])
            else:
                val = result[key]

            mqtt_single_out(f'{args.mqtt_topic}{base}/{key}', val)


def print_result(result):
    if args.mqtt:
        mqtt_iterator(result)
    else:
        print(json.dumps(result, indent=2))


# Initialize Daemon
if args.daemon:
    import time
    import systemd.daemon

    # Tell systemd that our service is ready
    systemd.daemon.notify(systemd.daemon.Notification.READY)

async def influx():
    token = "8NSTtcmBwEUUoOl5E3nhvoIOwIzZgNbUbOpdhN7UOMY452Y7srgClN5JZBerPSBBlelIR2Q6ZSukRqPg77GZOA=="
    org = "org"
    url = "http://192.168.88.2:8086"    
    write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
    
    bucket="bms"
    write_api = write_client.write_api(write_options=SYNCHRONOUS)

    i = 1
    while i < 1000:
        
        startTime = datetime.now()
        result = await bms.get_all()        
        stopTime = datetime.now()

        print_result(result)

        bmsRequestDuration = stopTime - startTime     

        timestamp = (startTime + ( (bmsRequestDuration) / 2))
           
        
        point = (
            Point("bms")
            .field("voltage", result['soc']['total_voltage'])
            .field("soc", result['soc']['soc_percent'])
            .field("current", result['soc']['current'])
            .field("capacity", result['mosfet_status']['capacity_ah'])
            .field("chargingEnabled", int(result['mosfet_status']['charging_mosfet']))
            .field("dischargingEnabled", int(result['mosfet_status']['discharging_mosfet']))
            .field("temperature", result['temperature_range']['highest_temperature'])
            #.field("cycles", result['status']['cycles'])
            .field("highestCellVoltage", result['cell_voltage_range']['highest_voltage'])
            .field("lowestCellVoltage", result['cell_voltage_range']['lowest_voltage'])
            .field("highestCellVoltageNumber", result['cell_voltage_range']['highest_cell'])
            .field("lowestCellVoltageNumber", result['cell_voltage_range']['lowest_cell'])
            #.field("cellVoltage01", result['cell_voltages'][1])
            #.field("cellVoltage02", result['cell_voltages'][2])
            #.field("cellVoltage03", result['cell_voltages'][3])
            #.field("cellVoltage04", result['cell_voltages'][4])
            #.field("cellVoltage05", result['cell_voltages'][5])
            #.field("cellVoltage06", result['cell_voltages'][6])
            #.field("cellVoltage07", result['cell_voltages'][7])
            #.field("cellVoltage08", result['cell_voltages'][8])
            #.field("cellVoltage09", result['cell_voltages'][9])
            #.field("cellVoltage10", result['cell_voltages'][10])
            #.field("cellVoltage11", result['cell_voltages'][11])  
            #.field("cellVoltage12", result['cell_voltages'][12])
            #.field("cellVoltage13", result['cell_voltages'][13])
            #.field("cellVoltage14", result['cell_voltages'][14])
            #.field("cellVoltage15", result['cell_voltages'][15])
            #.field("cellVoltage16", result['cell_voltages'][16])
            .time(int(timestamp.timestamp()), WritePrecision.S)
        )
        
        write_api.write(bucket=bucket, org="org", record=point)

        
        i += 1
        

        time.sleep(2)

    await bms.disconnect()


while True:
    if args.status:
        result = asyncio.run(bms.get_status())
        print_result(result)
    if args.soc:
        result = asyncio.run(bms.get_soc())
        print_result(result)
    if args.mosfet:
        result = asyncio.run(bms.get_mosfet())
        print_result(result)
    if args.cell_voltages:
        if not args.status:           
            asyncio.run(bms.get_status())
            result = asyncio.run(bms.get_cell_voltages())
            print_result(result)
    if args.cell_voltage_range:
        result = asyncio.run(bms.get_cell_voltage_range())
        print_result(result)
    if args.temperatures:
        result = asyncio.run(bms.get_temperatures())
        print_result(result)
    if args.balancing:
        result = asyncio.run(bms.get_balancing_status())
        print_result(result)
    if args.errors:
        result = asyncio.run(bms.get_errors())
        print_result(result)
    if args.all:
        result = asyncio.run(bms.get_all())
        print_result(result)
    
    if args.influx:
        asyncio.run(influx())

    if args.check:
        status = asyncio.run(bms.get_status())
        status_code = 0  # OK
        status_codes = ('OK', 'WARNING', 'CRITICAL', 'UNKNOWN')
        status_line = ''

        data = asyncio.run(bms.get_soc())
        perfdata = []
        if data:
            for key, value in data.items():
                perfdata.append('%s=%s' % (key, value))

                # todo: read errors

                if status_code == 0:
                    status_line = '%0.1f volt, %0.1f amper' % (data['total_voltage'], data['current'])

                    print("%s - %s | %s" % (status_codes[status_code], status_line, " ".join(perfdata)))
                    sys.exit(status_code)
    if args.set_discharge_mosfet:
        break #setting mosfets not part of the daemon loop
    if args.daemon:
        systemd.daemon.notify(systemd.daemon.Notification.WATCHDOG)
        print(f"Sleeping for {args.daemon_pause} sec")
        time.sleep(args.daemon_pause)
    else:
        logger.debug("Once off command, not looping")
        break


if args.set_discharge_mosfet:
    if args.set_discharge_mosfet == 'on':
        on = True
    elif args.set_discharge_mosfet == 'off':
        on = False
    else:
        print("invalid value '%s', expected 'on' or 'off'" % args.set_discharge_mosfet)
        sys.exit(1)

        result = asyncio.run(bms.set_discharge_mosfet(on=on))

if mqtt_client:
    mqtt_client.disconnect()
    mqtt_client.loop_stop()


if not result:
    sys.exit()

if args.daemon:
    systemd.daemon.notify(systemd.daemon.Notification.STOPPING)
