#!/usr/bin/python3
import asyncio
from datetime import datetime
import subprocess
import logging
import time
from bleak import BleakClient

from daly_bms import DalyBMS


class DalyBMSBluetooth(DalyBMS):
    def __init__(self, request_retries=3, logger=None):
        """

        :param request_retries: How often read requests should get repeated in case that they fail (Default: 3).
        :param logger: Python Logger object for output (Default: None)
        """
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
        DalyBMS.__init__(self, request_retries=request_retries, address=8, logger=logger)
        self.client = None
        self.response_cache = {}

    async def connect(self, mac_address):
        """
        Open the connection to the Bluetooth device.

        :param mac_address: MAC address of the Bluetooth device
        """
        try:
            """
            When an earlier execution of the script crashed, the connection to the devices stays open and future
            connection attempts would fail with this error:
            bleak.exc.BleakError: Device with address AA:BB:CC:DD:EE:FF was not found.
            see https://github.com/hbldh/bleak/issues/367
            
            out = subprocess.check_output("rfkill unblock bluetooth", shell = True)
            
            open_blue = subprocess.Popen(["bluetoothctl"], shell=True, stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, stdin=subprocess.PIPE)      
            open_blue.communicate(b"disconnect %s\n" % mac_address.encode('utf-8'))
            open_blue.kill()
            """

        except:
            pass

        self.logger.debug("Bluetooth connecting...")
        self.client = BleakClient(mac_address)
        connected = await self.client.connect()
        self.logger.info(f"Bluetooth connected: [{connected}]")

        """
        15
        """
        await self.client.start_notify('0000fff1-0000-1000-8000-00805f9b34fb', self._notification_callback)  
        
        return connected
        """
        48
        
        await self.client.write_gatt_char(48, bytearray(b""))
        """
    async def disconnect(self):
        """
        Disconnect from the Bluetooth device
        """
        self.logger.debug("Bluetooth disconnecting ...")
        if self.is_connected:
            disconnected = await self.client.disconnect()
            self.logger.info(f"Bluetooth connected: [{not disconnected}]")

    @property
    def is_connected(self) -> bool:
        """
        Check connection status between this client and the GATT server.

        Returns:
            Boolean representing connection status.

        """
        clientSet = self.client != None
        connected = False
        if clientSet:
                connected = self.client.is_connected
        result = clientSet and connected
        return result

    async def _read_request(self, command, max_responses=1):
        response_data = None
        x = 0
        for x in range(0, self.request_retries):
            response_data = await self._read(
                command=command,
                max_responses=max_responses)
            if not response_data:
                self.logger.debug("%x. try failed, retrying..." % (x + 1))
                await asyncio.sleep(0.2)
            else:
                break
        if not response_data:
            self.logger.error('%s failed after %s tries' % (command, x + 1))
            return False
        return response_data

    async def _read(self, command, max_responses=1):
        self.logger.debug("-- %s ------------------------" % command)
        self.response_cache[command] = {"queue": [],
                                        "future": asyncio.Future(),
                                        "max_responses": max_responses,
                                        "done": False}

        message_bytes = self._format_message(command)
        result = await self._async_char_write(command, message_bytes)
        self.logger.debug("got %s" % result)
        if not result:
            return False
        if max_responses == 1:
            return result[0]
        else:
            return result

    def _notification_callback(self, handle, data):
        self.logger.debug(f'Notify callback. Handle: {handle}, Data Length: {len(data)}, Data: {data}')
        responses = []

        num_frames = int(len(data) / 13)
        if num_frames == 0:
            self.logger.debug(f"{len(data)} bytes received, not enough for a data frame, discarding")

        for frame_start in range(0, num_frames*13, 13):
            # check that the data frame is properly formatted:
            if data[frame_start] == 0xa5 and data[frame_start + 1] == 0x01 and data[frame_start + 3] == 0x08:
                responses.append(data[frame_start:frame_start+13])

        for response_bytes in responses:
            command = response_bytes[2:3].hex()
            if self.response_cache[command]["done"] is True:
                self.logger.debug("skipping response for %s, done" % command)
                return
            self.response_cache[command]["queue"].append(response_bytes[4:-1])
            if len(self.response_cache[command]["queue"]) == self.response_cache[command]["max_responses"]:
                self.response_cache[command]["done"] = True
                self.response_cache[command]["future"].set_result(self.response_cache[command]["queue"])

    async def _async_char_write(self, command, value):
        if not self.client.is_connected:
            self.logger.info("Connecting...")
            await self.client.connect()

        await self.client.write_gatt_char('0000fff2-0000-1000-8000-00805f9b34fb', value)
        """
        15
        """
        self.logger.debug("Waiting...")
        try:
            result = await asyncio.wait_for(self.response_cache[command]["future"], 5)
        except asyncio.TimeoutError:
            self.logger.warning("Timeout while waiting for %s response" % command)
            return False
        self.logger.debug("got %s" % result)
        return result

    # wrap all sync functions so that they can be awaited
    async def get_soc(self, response_data=None):
        response_data = await self._read_request("90")
        return super().get_soc(response_data=response_data)

    async def get_cell_voltage_range(self, response_data=None):
        response_data = await self._read_request("91")
        return super().get_cell_voltage_range(response_data=response_data)

    async def get_max_min_temperature(self, response_data=None):
        response_data = await self._read_request("92")
        return super().get_temperature_range(response_data=response_data)

    async def get_mosfet_status(self, response_data=None):
        response_data = await self._read_request("93")
        return super().get_mosfet_status(response_data=response_data)

    async def get_status(self, response_data=None):
        response_data = await self._read_request("94")
        return super().get_status(response_data=response_data)

    async def get_cell_voltages(self, response_data=None):
        # required to get the number of cells
        if not self.status:
            await self.get_status()

        max_responses = 6 # self._calc_num_responses(status_field="cell_voltages")
        if not max_responses:
            return
        response_data = await self._read_request("95", max_responses=max_responses)

        return super().get_cell_voltages(response_data=response_data)

    async def get_temperatures(self, response_data=None):

        max_responses = self._calc_num_responses(status_field="temperatures")
        if not max_responses:
            return

        response_data = await self._read_request("96", max_responses=max_responses)
        return super().get_temperatures(response_data=response_data)

    async def get_balancing_status(self, response_data=None):
        response_data = await self._read_request("97")
        return super().get_balancing_status(response_data=response_data)

    async def get_errors(self, response_data=None):
        response_data = await self._read_request("98")
        return super().get_errors(response_data=response_data)

    async def get_all(self):
        soc = await self.get_soc()
        time.sleep(1)
        cell_voltage_range = await self.get_cell_voltage_range()
        time.sleep(1)
        temperature_range = await self.get_max_min_temperature()
        time.sleep(1)
        mosfet_status = await self.get_mosfet_status()
        time.sleep(1)
        #status = await self.get_status()
        #cell_voltages = await self.get_cell_voltages()
        #temperatures = await self.get_temperatures()
        #balancing_status = await self.get_balancing_status()
        errors = await self.get_errors()

        return {
            "timestamp": datetime.now().isoformat(),
            "soc": soc,
            "cell_voltage_range": cell_voltage_range,
            "temperature_range": temperature_range,
            "mosfet_status": mosfet_status,
            #"status": status,
            #"cell_voltages": await self.get_cell_voltages(),
            #"temperatures": await self.get_temperatures(),
            #"balancing_status": await self.get_balancing_status(),
            "errors": errors
        }
