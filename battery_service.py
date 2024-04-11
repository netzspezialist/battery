import asyncio
import json
import os
import signal
import sys
import time
import logging

from datetime import datetime

from daly_bluetooth_connection import DalyBluetoothConnection
from config import minimumRequestDelaySeconds

from battery_influx import BatteryInflux

class BatteryService:
    #FIFO = '/tmp/bms_service_pipe'

    def __init__(self, logger = None):
        self.logger = logger

        self.bms = DalyBluetoothConnection(self.logger)
        self.influx = BatteryInflux(self.logger)

        #if not os.path.exists(BMS_Service.FIFO):
        #    os.mkfifo(BMS_Service.FIFO)
        #self.fifo = os.open(BMS_Service.FIFO, os.O_RDWR | os.O_NONBLOCK)
        #signal.signal(signal.SIGTERM, self._handle_sigterm)
        self.logger.info('BMS service instance created')    

    async def start(self):
        self.logger.info('Starting bms service...')
        self.serviceRunning = True
        await self.loop()

    def stop(self):
        self.logger.info('Stopping bms service...')
        self.serviceRunning = False
        #if os.path.exists(BMS_Service.FIFO):
        #    os.close(self.fifo)
        #    os.remove(BMS_Service.FIFO)
        #    self.logger.info('Named pipe removed')
        #else:
        #    self.logger.error('Named pipe not found, nothing to clean up')
                

    #def _handle_sigterm(self, sig, frame):
    #    self.logger.warning('SIGTERM received...')
    #    service.stop()


    async def loop(self):
        start = time.time()
        elapsedSeconds = 86400 # read all values at least at service start
        elapsedSecondsSoc = 0
        elapsedSecondsCellVoltageRange = 0
        elapsedSecondsTemperature = 0
        elapsedSecondsCellVoltages = 0
        exceptionCounter = 0
        while self.serviceRunning:            
            try:                
                # soc
                elapsedSecondsSoc = elapsedSecondsSoc + elapsedSeconds
                if elapsedSecondsSoc > minimumRequestDelaySeconds["soc"]:
                    await self.soc()
                    elapsedSecondsSoc = 0

                # cell_voltage_range
                elapsedSecondsCellVoltageRange = elapsedSecondsCellVoltageRange + elapsedSeconds
                if elapsedSecondsCellVoltageRange > minimumRequestDelaySeconds["cellVoltageRange"]:
                    await self.cell_voltage_range()
                    elapsedSecondsCellVoltageRange = 0

                # temperature
                elapsedSecondsTemperature = elapsedSecondsTemperature + elapsedSeconds
                if elapsedSecondsTemperature > minimumRequestDelaySeconds["temperature"]:
                    await self.temperature()
                    elapsedSecondsTemperature = 0

                # cell_voltages
                elapsedSecondsCellVoltages = elapsedSecondsCellVoltages + elapsedSeconds
                if elapsedSecondsCellVoltages > minimumRequestDelaySeconds["cellVoltages"]:
                    await self.cell_voltages()
                    elapsedSecondsCellVoltages = 0

                await self.bms.disconnect()

                end = time.time()
                elapsedSeconds = end - start
                start = time.time()
                
                await asyncio.sleep(2)
                    
            except Exception as e:
                self.logger.error(f'Error in loop: {e}')
                exceptionCounter = exceptionCounter + 1
                await asyncio.sleep(10)

                if exceptionCounter > 5:
                    self.logger.error('Too many exceptions, stopping service')  
                    raise SystemExit
            

        self.logger.info('BMS work loop stopped')

    async def soc(self):
        self.logger.info('Getting SOC...')
        startTime = datetime.now()
        result = await self.bms.get_soc()
        stopTime = datetime.now()

        self.logger.info(f'SOC result: {result}')

        bmsRequestDuration = stopTime - startTime     

        timestamp = (startTime + ( (bmsRequestDuration) / 2))

        soc = result['soc_percent']
        voltage = result['total_voltage']
        current = result['current']

        await self.influx.upload_soc(timestamp, soc, voltage, current)

    async def cell_voltage_range(self):
        self.logger.debug('Getting cell voltage range...')
        startTime = datetime.now()
        result = await self.bms.get_cell_voltage_range()
        stopTime = datetime.now()

        self.logger.info(f'cell_voltage_range result: {result}')

        bmsRequestDuration = stopTime - startTime     

        timestamp = (startTime + ( (bmsRequestDuration) / 2))

        highest_voltage = result['highest_voltage']
        highest_cell = result['highest_cell']
        lowest_voltage = result['lowest_voltage']
        lowest_cell = result['lowest_cell']

        await self.influx.upload_cell_voltage_range(timestamp, highest_voltage, highest_cell, lowest_voltage, lowest_cell)

    async def temperature(self):
        self.logger.debug('Getting temperature...')
        startTime = datetime.now()
        result = await self.bms.get_temps()
        stopTime = datetime.now()

        self.logger.info(f'temperature result: {result}')

        bmsRequestDuration = stopTime - startTime     

        timestamp = (startTime + ( (bmsRequestDuration) / 2))

        temperature = result['highest_temperature']

        await self.influx.upload_temperature(timestamp, temperature)

    async def cell_voltages(self):
        self.logger.debug('Getting cell voltages...')
        startTime = datetime.now()
        result = await self.bms.get_cell_voltages()        
        stopTime = datetime.now()

        self.logger.info(f'cell voltages result: {result}')

        bmsRequestDuration = stopTime - startTime     

        timestamp = (startTime + ( (bmsRequestDuration) / 2))

        voltages = []

        cells = len(result)
        print(cells)

        for i in range(1, cells + 1):
            voltages.append(result[i])

        await self.influx.upload_cell_voltages(timestamp, voltages)        

#    def _handle_sigterm(self, sig, frame):
#        self.logger.warning('SIGTERM received...')
#        asyncio.ensure_future(self.stop())